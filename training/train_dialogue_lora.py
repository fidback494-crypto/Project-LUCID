"""QLoRA supervised fine-tuning for LUCID's reviewed Korean dialogue corpus."""

import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fine-tune the matching Qwen Instruct base with a LoRA adapter."
    )
    parser.add_argument("--train-file", required=True, type=Path)
    parser.add_argument("--validation-file", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("/content/lucid-qwen-lora"), type=Path)
    parser.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--epochs", default=3, type=int)
    parser.add_argument("--max-length", default=2048, type=int)
    parser.add_argument("--allow-small-pilot", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA 실행에 GPU가 필요해. Colab에서 T4 런타임을 선택해줘.")
    if not args.train_file.is_file() or not args.validation_file.is_file():
        raise FileNotFoundError("학습용과 검증용 JSONL 파일 경로를 확인해줘.")

    datasets = load_dataset(
        "json",
        data_files={
            "train": str(args.train_file),
            "validation": str(args.validation_file),
        },
    )
    train_count = len(datasets["train"])
    validation_count = len(datasets["validation"])
    if train_count < 100 or validation_count < 20:
        message = (
            f"현재 데이터는 train={train_count}, validation={validation_count}개야. "
            "최종 학습 전에는 검수한 다중 턴 대화를 더 모아줘."
        )
        if not args.allow_small_pilot:
            raise ValueError(message + " 작은 형식 확인만 하려면 --allow-small-pilot을 사용해.")
        print("주의:", message)

    for split_name in ("train", "validation"):
        for row_number, row in enumerate(datasets[split_name], start=1):
            if not isinstance(row.get("prompt"), list) or not isinstance(row.get("completion"), list):
                raise ValueError(f"{split_name} {row_number}번째 행은 prompt/completion 메시지 배열이 필요해.")
            if not row["prompt"] or not row["completion"]:
                raise ValueError(f"{split_name} {row_number}번째 행에 빈 prompt/completion이 있어.")
            if row["prompt"][-1].get("role") != "user":
                raise ValueError(f"{split_name} {row_number}번째 prompt는 user 메시지로 끝나야 해.")
            if any(message.get("role") != "assistant" for message in row["completion"]):
                raise ValueError(f"{split_name} {row_number}번째 completion은 assistant 메시지만 포함해야 해.")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=quantization,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.config.use_cache = False

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )
    training = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        weight_decay=0.01,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        max_length=args.max_length,
        completion_only_loss=True,
        packing=False,
        report_to="none",
        seed=42,
    )

    trainer = SFTTrainer(
        model=model,
        args=training,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        processing_class=tokenizer,
        peft_config=lora,
    )
    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    print(f"LoRA 어댑터 저장 완료: {args.output_dir.resolve()}")
    print("Ollama 적용 전에는 이 어댑터가 같은 Qwen 베이스 모델과 짝인지 확인해줘.")


if __name__ == "__main__":
    main()

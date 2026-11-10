# LUCID Korean dialogue data

This folder is for teaching LUCID conversational behavior. It is separate from
`data/lucid_memory.db`, which stores changing user facts and actual conversation
episodes.

## Data format

Each JSONL row is a conversational prompt and one target assistant turn:

- `prompt`: system instructions plus the prior user/assistant turns and the
  current user turn.
- `completion`: one assistant message containing the JSON object LUCID returns
  internally. Only `reply` is shown in the chat; `speech_style` is passed to the
  Korean TTS service.

The format matches the conversational prompt/completion format supported by
Hugging Face TRL's SFT trainer. Keep previous assistant turns as plain visible
Korean text, as LUCID stores them that way. The final completion must follow the
current cognitive response schema.

## What examples should teach

Write multi-turn Korean conversations that show LUCID how to:

- respond to what was just said, without greeting the user again every turn;
- ask at most one natural follow-up when it helps the conversation;
- react with warmth or curiosity without turning every reply into a question;
- adapt between casual speech, polite speech, and half-polite speech to fit the
  situation;
- acknowledge corrections and topic changes without defending the old answer;
- be honest about unknown facts and avoid inventing shared memories;
- express its dream-between-worlds character lightly, without repeating lore in
  ordinary conversation;
- keep visible dialogue natural while returning the internal JSON fields.

Start with the reviewed examples in `seed.jsonl`, then expand toward 300–500
distinct, high-quality turns before fine-tuning. Prefer varied 2–6 turn scenes
over many isolated greetings. Do not copy unreviewed logs, private user details,
or bad model replies into the target answers. Add the same `scene_id` to rows
from one conversation so the splitter keeps that entire scene in only one split.

Prepare the reviewed corpus (keep this source file out of Git if it contains
private or unreleased material):

```powershell
python training/split_dialogue_data.py --input path/to/reviewed.jsonl --output-dir path/to/lucid-split
```

The splitter writes `train.jsonl` and `validation.jsonl`. The training script
requires at least 100 training rows and 20 validation rows unless
`--allow-small-pilot` is explicitly set. Do not treat a pilot on the 15 seed rows
as evidence that the model is ready for daily use.

Run the prepared split on a Colab T4 after installing the separate training
dependencies:

```bash
pip install -r requirements-training.txt
python training/train_dialogue_lora.py \
  --train-file path/to/lucid-split/train.jsonl \
  --validation-file path/to/lucid-split/validation.jsonl
```

## Keep information in the right place

- Stable identity and roleplay rules belong in `src/self/identity.py` and the
  system prompt.
- User-specific facts and real past interactions belong in SQLite memory.
- This dataset should teach response habits, not make the model believe that a
  particular example user is the real user.
- Korean TTS is a separate model. Training this dataset does not train the voice.

## Fine-tuning

Use supervised fine-tuning with a LoRA/QLoRA adapter based on
`Qwen/Qwen2.5-3B-Instruct`, matching the `qwen2.5:3b` inference family. Keep the
base model and adapter matched. Do not train the full model for the first pass.
After the data is curated, use a Colab T4 run as a small pilot and save the
adapter outside the project data folder. Compare it with the untuned model on
held-out dialogues before deployment. Ollama may require a merged or converted
model; check its current Qwen adapter support before assuming the Safetensors
adapter can be loaded directly.

The small `seed.jsonl` file is a format and style starting point, not a
production-ready fine-tuning corpus.

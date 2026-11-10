import os
import getpass
from urllib.parse import urlsplit

from src.app.lucid import LucidEngine


def configure_ollama_address():

    print("Ollama 서버 주소 설정")
    print("주소를 입력하면 이번 실행에 적용해. Enter를 누르면 기존 설정 또는 기본 주소를 사용해.")

    while True:
        address = input("Ollama 주소: ").strip()

        if not address:
            return

        address = address.rstrip("/")

        try:
            parsed = urlsplit(address)
            is_valid = (
                parsed.scheme in {"http", "https"}
                and parsed.netloc
                and parsed.hostname
                and not any(character.isspace() for character in address)
            )
        except ValueError:
            is_valid = False

        if not is_valid:
            print("http:// 또는 https:// 로 시작하는 서버 주소를 입력해줘.")
            continue

        os.environ["LUCID_OLLAMA_URL"] = address
        print("이번 실행에 사용할 Ollama 주소를 설정했어.")
        return


def configure_korean_tts_address():

    print("\n한국어 음성 서버 주소 설정")
    print("한국어 Qwen3-TTS Colab의 Cloudflare 터널 주소를 입력해.")
    print("Enter를 누르면 기존 설정 또는 로컬 기본 주소를 사용해.")

    while True:
        address = input("한국어 TTS 주소: ").strip()

        if not address:
            return

        address = address.rstrip("/")

        try:
            parsed = urlsplit(address)
            is_valid = (
                parsed.scheme in {"http", "https"}
                and parsed.netloc
                and parsed.hostname
                and not any(character.isspace() for character in address)
            )
        except ValueError:
            is_valid = False

        if not is_valid:
            print("http:// 또는 https:// 로 시작하는 서버 주소를 입력해줘.")
            continue

        os.environ["LUCID_TTS_URL"] = address
        token = getpass.getpass("Colab에 표시된 한국어 TTS 토큰: ").strip()
        if token:
            os.environ["LUCID_TTS_TOKEN"] = token
        speaker = input("화자 이름 [Sohee]: ").strip() or "Sohee"
        os.environ["LUCID_TTS_SPEAKER"] = speaker
        print(f"이번 실행은 한국어 TTS의 {speaker} 음성을 사용하도록 설정했어.")
        return


def main():

    configure_ollama_address()
    configure_korean_tts_address()

    lucid = LucidEngine()

    lucid.boot()

    lucid.run()


if __name__ == "__main__":
    main()

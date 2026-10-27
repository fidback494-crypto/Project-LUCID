import os
from urllib.parse import urlsplit

from src.app.lucid import LucidEngine


def configure_ollama_address():

    print("Ollama 서버 주소 설정")
    print("주소를 입력하면 이번 실행에 적용하고, Enter를 누르면 기존 설정을 사용해.")

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


def main():

    configure_ollama_address()

    lucid = LucidEngine()

    lucid.boot()

    lucid.run()


if __name__ == "__main__":
    main()

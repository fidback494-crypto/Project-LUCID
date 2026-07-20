from src.engine.lucid_engine import LucidEngine


def main():
    engine = LucidEngine()

    print("=" * 40)
    print("LUCID AI")
    print("=" * 40)

    print("Engine Loaded Successfully!")
    print(engine.state.status())


if __name__ == "__main__":
    main()
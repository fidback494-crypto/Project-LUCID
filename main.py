from src.engine.lucid_engine import LucidEngine


def main():
    lucid = LucidEngine()

    lucid.boot()

    lucid.run()


if __name__ == "__main__":
    main()
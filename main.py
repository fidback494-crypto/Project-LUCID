from src.app.lucid import LucidEngine


def main():

    lucid = LucidEngine()

    lucid.boot()

    lucid.run()


if __name__ == "__main__":
    main()
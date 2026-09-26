from .parser import main_parser


def main() -> None:
    print(main_parser())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)

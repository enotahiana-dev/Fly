from .parser import get_network


def main() -> None:
    print(get_network())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error: ", e)

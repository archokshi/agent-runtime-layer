from pathlib import Path


def main() -> None:
    path = Path("app.py")
    path.write_text(path.read_text(encoding="utf-8") + "\n# mock aider edit\n", encoding="utf-8")
    print("mock aider changed app.py")


if __name__ == "__main__":
    main()

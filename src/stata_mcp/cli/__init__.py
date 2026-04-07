def main() -> None:
    """Run the command line entrypoint."""
    from ._cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()

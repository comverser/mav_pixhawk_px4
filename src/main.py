"""CLI entry point"""
import asyncio
import sys
from src.commands import flight, shell


def main(argv: list[str] = None) -> None:
    """Main entry point."""
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        asyncio.run(flight.takeoff())
    elif args[0] == "takeoff":
        asyncio.run(flight.takeoff())
    elif args[0] == "shell" and len(args) > 1:
        asyncio.run(shell.execute(' '.join(args[1:])))
    else:
        print(f"Unknown command: {args[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()

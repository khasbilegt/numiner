import argparse

from pathlib import Path
from pprint import pprint

from numiner import __version__


def existing_path(arg: str) -> Path:
    path = Path(arg)

    if not path.exists():
        raise argparse.ArgumentTypeError(f"Couldn't find {arg}. Check and try again.")

    return path


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS] | [<path_1>] ... [<path_N>]", allow_abbrev=False
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    parser.add_argument(
        "path",
        nargs="+",
        type=existing_path,
        help="A path(s) to a folder or a sheet that's holding the data to mine",
    )
    return parser.parse_args()


def main():
    args = get_args()
    pprint(args)


if __name__ == "__main__":
    main()

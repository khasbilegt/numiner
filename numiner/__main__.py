import argparse

from pathlib import Path

from numiner import __version__
from numiner.classes.sheet import Sheet


def existing_dir_path(arg):
    path = Path(arg)
    if path.exists() and path.is_dir():
        return path
    raise argparse.ArgumentTypeError(
        f"Either couldn't find or it's not a directory. Check and try again."
    )


def get_args():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS] | [<source_dir>] [<result_dir>]", allow_abbrev=False
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "source",
        type=existing_dir_path,
        help="a path to a folder that's holding the <source> sheet images",
    )
    parser.add_argument(
        "result",
        type=existing_dir_path,
        help="a path to a folder where all <result> images will be saved",
    )
    return parser.parse_args()


def main():
    args = get_args()

    sheets = tuple(
        Sheet(path, args.result)
        for path in tuple(
            path
            for path in tuple(args.source.iterdir())
            if path.stem.startswith("SHEET") and path.suffix in (".jpg", ".png", "jpeg")
        )
    )

    for sheet in sheets:
        sheet.process_sheet(save=True)


if __name__ == "__main__":
    main()

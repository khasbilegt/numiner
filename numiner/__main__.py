import argparse

from pathlib import Path
from typing import Tuple

from numiner import __version__
from numiner.classes.sheet import Sheet


def existing_dir_path(arg: str) -> Path:
    path = Path(arg)
    if path.exists() and path.is_dir():
        return path
    raise argparse.ArgumentTypeError(
        f"Either couldn't find or it's not a directory. Check and try again."
    )


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS] | [<source_dir>] [<result_dir>]", allow_abbrev=False
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
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
    args: argparse.Namespace = get_args()

    sheets: Tuple[Sheet] = tuple(
        Sheet(path)
        for path in tuple(
            path
            for path in tuple(args.source.iterdir())
            if path.stem.startswith("SHEET") and path.suffix in (".jpg", ".png", "jpeg")
        )
    )

    Sheet.show(
        images=[sheets[0].get_original_img(), sheets[0].blur()],
        positions=[121, 122],
        titles=["Original", "Blurred"],
        total=2,
    )


if __name__ == "__main__":
    main()

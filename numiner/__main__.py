import argparse
import logging
import sys

from pathlib import Path

from numiner import __version__
from numiner.classes.letter import Letter
from numiner.classes.sheet import Sheet


def setup_log(path, option):
    logging.basicConfig(
        filename=path / f"numiner_{option}.log",
        level=logging.INFO,
        format="%(asctime)s :%(name)s: %(message)s",
        datefmt="%Y/%m/%d %I:%M:%S %p",
    )


def existing_path(arg):
    path = Path(arg)
    if path.exists() and (path.is_dir() or path.is_file()):
        return path
    raise argparse.ArgumentTypeError(
        "Either couldn't find or it's neither a directory nor a file. Check and try again."
    )


def existing_json_file(arg):
    path = Path(arg)
    if path.exists() and path.is_file() and path.suffix == ".json":
        return path
    raise argparse.ArgumentTypeError("Invalid path to config json file. Check and try again.")


def create_argparser():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-s",
        "--sheet",
        nargs=2,
        metavar=("<source>", "<result>"),
        type=existing_path,
        help="a path to a folder or file that's holding the <source> sheet image(s) &\
             a path to a folder where all <result> images will be saved",
    )
    parser.add_argument(
        "-l",
        "--letter",
        nargs=2,
        metavar=("<source>", "<result>"),
        type=existing_path,
        help="a path to a folder or a file that's holding the cropped image(s) &\
             a path to a folder where all <result> images will be saved",
    )
    parser.add_argument(
        "-c",
        dest="labels",
        metavar="<path>",
        type=existing_json_file,
        help="a path to .json file that's holding top to bottom, left to right labels of the sheet with their ids",
    )
    return parser


def handle_letter(path):
    source = path[0]
    result = path[1]

    setup_log(result, "letter")

    if source.is_dir():
        for path in (
            path for path in tuple(source.rglob("**/*")) if path.suffix in (".jpg", ".png", "jpeg")
        ):
            label = str(path.parent).split("/")[-1]
            letter = Letter(path, result, label=label)
            letter.process(save=True)
    else:
        label = str(source.parent).split("/")[-1]
        letter = Letter(source, result, label=label)
        letter.process(save=True)


def handle_sheet(path):
    source = path[0]
    result = path[1]

    setup_log(result, "sheet")

    if source.is_dir():
        sheets = tuple(
            Sheet(path, result)
            for path in tuple(
                path
                for path in tuple(source.iterdir())
                if path.stem.startswith("SHEET")
                and len(path.stem.split("_")) >= 2
                and path.suffix in (".jpg", ".png", "jpeg")
            )
        )

        for sheet in sheets:
            sheet.process_sheet(save=True)
    else:
        if source.stem.startswith("SHEET") and source.suffix in (".jpg", ".png", "jpeg"):
            sheet = Sheet(source, result)
            sheet.process_sheet(save=True)
        else:
            raise RuntimeError(f"The given sheet ({source}) is invalid.")


def handle_config(arg):
    import json

    with open(arg) as config_file:
        config = json.load(config_file)
        Sheet._CHARACTER_SEQUENCE = tuple(config["labels"].items())

    return Sheet._CHARACTER_SEQUENCE


def handle_empty_args(args, parser):
    if len(tuple(value for key, value in vars(args).items() if value is None)) == len(vars(args)):
        parser.print_help()
        sys.exit()


def get_version():
    print(__version__)


def main():
    parser = create_argparser()
    args = parser.parse_args()

    handle_empty_args(args, parser)

    if args.labels:
        handle_config(args.labels)

    if args.sheet:
        handle_sheet(args.sheet)

    if args.letter:
        handle_letter(args.letter)


if __name__ == "__main__":
    main()

from argparse import ArgumentTypeError
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from pytest import raises

from numiner.__main__ import existing_dir_path
from numiner.__main__ import get_args


def test_parser():
    with patch("sys.argv", ["numiner", "numiner", "tests"]):
        args = get_args()
        assert args == Namespace(source=Path("numiner"), result=Path("tests"))


def test_existing_dir_path():
    true_path = "numiner"
    false_path = "source"
    file_path = "/source/sheet.jpg"

    assert existing_dir_path(true_path) == Path(true_path)
    with raises(ArgumentTypeError):
        assert existing_dir_path(false_path)

    with raises(ArgumentTypeError):
        assert existing_dir_path(file_path)

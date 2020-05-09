from argparse import ArgumentTypeError
from pathlib import Path

import pytest

from numiner import __version__
from numiner.__main__ import (
    create_argparser,
    existing_json_file,
    existing_path,
    handle_config,
    handle_empty_args,
    handle_letter,
    handle_sheet,
)


@pytest.fixture
def example_sheet(tmp_path):
    source = tmp_path
    result = tmp_path / "result"
    for path in ((tmp_path / name) for name in ("SHEET_10_10_0.png", "SHEET_0.png", "3.png")):
        if not path.exists():
            path.touch()

    return (source, result)


@pytest.fixture
def example_letter(tmp_path):
    source = tmp_path
    result = tmp_path / "result"
    for path in ((tmp_path / name) for name in ("1.png", "2.png", "3.png")):
        if not path.exists():
            path.touch()

    return (source, result)


@pytest.fixture
def example_labels(tmp_path):
    import json

    path = tmp_path / "config.json"
    if not path.exists():
        path.touch()

    with open(path, "w") as file:
        data = {}
        data["labels"] = dict(A=1, B=2, C=3)
        json.dump(data, file)
    return (data, path)


def test_existing_path(tmp_path):
    true_path = tmp_path
    false_path = "source"
    file_path = tmp_path / "sheet.jpg"
    if not file_path.exists():
        file_path.touch()

    assert existing_path(true_path) == Path(true_path)
    assert existing_path(file_path) == Path(file_path)

    with pytest.raises(ArgumentTypeError):
        assert existing_path(false_path)


def test_valid_existing_json_file(tmp_path):
    path = tmp_path / "labels.json"
    if not path.exists():
        path.touch()
    assert existing_json_file(path) == path


@pytest.mark.parametrize("input", [Path(""), Path("labels.txt"), Path("labels.json")])
def test_invalid_existing_json_file(input, tmp_path):
    input = tmp_path / input
    with pytest.raises(ArgumentTypeError):
        assert existing_json_file(input)


@pytest.mark.parametrize("argv", ["-s", "--sheet", "-l", "--letter", "-c", "-v", "--version"])
def test_create_argparser(argv, tmp_path, capsys):
    parser = create_argparser()

    if argv in ("-s", "--sheet", "-l", "--letter"):
        inputs = []
        outputs = []
        for source in (tmp_path, tmp_path / "source.jpg"):
            if not source.exists():
                source.touch()

            inputs.append([argv, str(source), str(tmp_path)])
            outputs.append([source, tmp_path])

        for input, output in zip(inputs, outputs):
            args = parser.parse_args(input)
            assert args.letter == output if argv in ("-l", "--letter") else args.sheet == output

    elif argv in ("-v", "--version"):
        with pytest.raises(SystemExit):
            assert parser.parse_args([argv])
    else:
        path = tmp_path / "config.json"
        if not path.exists():
            path.touch()
        args = parser.parse_args([argv, str(path)])
        assert args.labels == path


def test_handle_empty_args():
    parser = create_argparser()
    args = parser.parse_args([])
    with pytest.raises(SystemExit):
        assert handle_empty_args(args, parser)


def test_handle_letter(example_letter, capsys):
    source, result = example_letter

    handle_letter(example_letter)
    captured = capsys.readouterr()
    for img in (item for item in source.iterdir() if item.suffix == ".png"):
        assert f"[!] Ignored letter - {str(img)}" in captured.out

    handle_letter((Path(source / "1.png"), result))
    captured = capsys.readouterr()
    assert f"[!] Ignored letter - {str(source / '1.png')}" == captured.out.replace("\n", "")


def test_handle_sheet(example_sheet, capsys):
    source, result = example_sheet

    handle_sheet(example_sheet)
    captured = capsys.readouterr()
    for img in (
        item for item in source.iterdir() if item.stem.startswith("SHEET") and item.suffix == ".png"
    ):
        assert f"[!] Couldn't save sheet - {str(img)}" in captured.out

    handle_sheet((Path(source / "SHEET_10_10_0.png"), result))
    captured = capsys.readouterr()
    assert f"[!] Couldn't save sheet - {str(source / 'SHEET_10_10_0.png')}" in captured.out.replace(
        "\n", ""
    )


def test_config_labels(example_labels):
    data, path = example_labels
    assert path.exists() is True
    seq = handle_config(path)
    assert seq == tuple(data["labels"].items())


def test_version():
    assert __version__ == "0.1.1"

import sys

import pytest

from text2qti.cmdline import main
from text2qti.err import Text2qtiError


def test_directory_input_raises_clean_error(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["text2qti", str(tmp_path)])
    with pytest.raises(Text2qtiError, match="is a directory"):
        main()


def test_missing_file_raises_clean_error(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["text2qti", str(tmp_path / "nope.txt")])
    with pytest.raises(Text2qtiError, match="does not exist"):
        main()

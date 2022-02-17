import functools
import subprocess
import sys
import textwrap
from pathlib import PurePath

import pytest  # type: ignore

import typing_asserts

OUR_PACKAGE = PurePath(typing_asserts.__file__).parent.parent

subprocess_run = functools.partial(
    subprocess.run, check=True, capture_output=True, text=True
)


@pytest.fixture
def venv_bin(cache) -> PurePath:
    venv_dir = PurePath(
        cache.makedir(f"venv{'.'.join(map(str, sys.version_info[:2]))}")
    )
    cmd = [sys.executable, "-m", "virtualenv", "-p", sys.executable, str(venv_dir)]
    subprocess_run(cmd)
    bin_dir = venv_dir / ("bin" if sys.platform != "win32" else "Scripts")
    return bin_dir


@pytest.mark.parametrize(
    "mypy_version, highest_py_version",
    [
        (900, (3, 10)),
        (800, (3, 9)),
        (730, (3, 8)),
        (700, (3, 7)),
    ],
)
def test_works_with_mypy(venv_bin, tmp_path, mypy_version, highest_py_version) -> None:
    # The first digit of mypy is a signal of the lowest Python supported version
    if sys.version_info[:2] > highest_py_version:
        pytest.skip("Python version too high!")

    subprocess_run([venv_bin / "pip", "install", "-U", OUR_PACKAGE])
    subprocess_run([venv_bin / "pip", "install", "-U", f"mypy==0.{mypy_version}"])
    (tmp_path / "mypy.ini").write_text(
        textwrap.dedent(
            """\
            [mypy]
            plugins = typing_asserts.mypy_plugin
        """
        )
    )
    (tmp_path / "badfile.py").write_text(
        textwrap.dedent(
            """\
            from typing import Any
            from typing_asserts import assert_type

            assert_type(1)
            assert_type[float](1)
            assert_type[Any](1)
        """
        )
    )
    (tmp_path / "goodfile.py").write_text(
        textwrap.dedent(
            """\
            from typing import Any
            from typing_asserts import assert_type

            def untyped_func():
                pass

            anyvar: Any = None

            assert_type[int](1)
            assert_type[float](1.0)
            assert_type[None](None)
            assert_type[Any](untyped_func())
            assert_type[Any](anyvar)
        """
        )
    )

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess_run(
            [str(venv_bin / "mypy"), "badfile.py", "goodfile.py"], cwd=tmp_path
        )

    output = exc_info.value.output
    output_lines = output.splitlines()

    assert "INTERNAL ERROR" not in output
    assert "goodfile.py" not in output
    assert (
        f"badfile.py:4: error: You must provide a type parameter to 'assert_type'"
        in output_lines[0]
    )
    assert (
        f"badfile.py:5: error: assert_type failed. expected: 'builtins.float', actual 'builtins.int'"
        in output_lines[1]
    )
    assert (
        f"badfile.py:6: error: assert_type failed. expected: 'Any', actual 'builtins.int'"
        in output_lines[2]
    )

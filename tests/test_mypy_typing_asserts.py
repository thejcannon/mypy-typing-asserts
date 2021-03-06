import functools
import random
import subprocess
import sys
import textwrap
from pathlib import PurePath
from typing import Dict

import pytest  # type: ignore

import mypy_typing_asserts

OUR_PACKAGE = PurePath(mypy_typing_asserts.__file__).parent.parent

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
            plugins = mypy_typing_asserts.mypy_plugin
        """
        )
    )
    (tmp_path / "badfile.py").write_text(
        textwrap.dedent(
            """\
            from typing import Any, Dict
            from mypy_typing_asserts import assert_type

            int_var: int = 1
            stringdict_var: Dict[str, str] = {}

            assert_type(1)
            assert_type[float](int_var)
            assert_type[Any](int_var)
            assert_type[Dict](stringdict_var)
        """
        )
    )
    (tmp_path / "goodfile.py").write_text(
        textwrap.dedent(
            """\
            from typing import Any, Dict
            from mypy_typing_asserts import assert_type

            def untyped_func():
                pass

            anyvar: Any = None

            int_var: int = 0
            float_var: float = 1.0
            stringdict_var: Dict[str, str] = {}

            assert_type[int](int_var)
            assert_type[float](float_var)
            assert_type[None](None)
            assert_type[Any](untyped_func())
            assert_type[Any](anyvar)
            assert_type[Dict[str, str]](stringdict_var)
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
        "badfile.py:7: error: You must provide a type parameter to 'assert_type'"
        in output_lines[0]
    )
    assert (
        "badfile.py:8: error: assert_type failed. expected: 'builtins.float*', actual 'builtins.int'"
        in output_lines[1]
    )
    assert (
        "badfile.py:9: error: assert_type failed. expected: 'Any', actual 'builtins.int'"
        in output_lines[2]
    )
    assert (
        "badfile.py:10: error: assert_type failed. expected: 'builtins.dict*[Any, Any]', actual 'builtins.dict[builtins.str, builtins.str]"
        in output_lines[3]
    )


def test_returns_the_arg() -> None:
    def returns_int() -> int:
        return random.randint(0, 10)

    intvar: int = 1

    assert mypy_typing_asserts.assert_type[None](None) is None
    assert mypy_typing_asserts.assert_type[int](intvar) == 1
    assert isinstance(mypy_typing_asserts.assert_type[int](returns_int()), int)

    # This tests that our plugin also coerces the return type, otherwise we'd hit
    # https://github.com/python/mypy/issues/1020
    assert (
        mypy_typing_asserts.assert_type[int](
            mypy_typing_asserts.assert_type[int](intvar)
        )
        == 1
    )

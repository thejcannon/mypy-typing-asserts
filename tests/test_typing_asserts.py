from pathlib import PurePath
import subprocess
import sys
import textwrap
import functools

import pytest

import typing_asserts

OUR_PACKAGE = PurePath(typing_asserts.__file__).parent.parent

subprocess_run = functools.partial(
    subprocess.run, check=True, capture_output=True, text=True
)


@pytest.fixture
def venv_bin(cache):
    venv_dir = PurePath(
        cache.makedir(f"venv{'.'.join(map(str, sys.version_info[:2]))}")
    )
    cmd = [sys.executable, "-m", "virtualenv", "-p", sys.executable, str(venv_dir)]
    subprocess_run(cmd)
    bin_dir = venv_dir / ("bin" if sys.platform != "win32" else "Scripts")
    subprocess_run([bin_dir / "pip", "install", OUR_PACKAGE])
    return bin_dir


@pytest.mark.parametrize(
    "mypy_version",
    [
        "0.930",
        "0.900",
    ],
)
def test_works_with_mypy(venv_bin, tmp_path, mypy_version):
    subprocess_run([venv_bin / "pip", "install", "-U", f"mypy=={mypy_version}"])
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [tool.mypy]
            plugins = "typing_asserts.mypy_plugin"
        """
        )
    )
    (tmp_path / "myfile.py").write_text(
        textwrap.dedent(
            """\
            from typing_asserts import assert_type

            assert_type[float](1)
        """
        )
    )

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess_run([str(venv_bin / "mypy"), "myfile.py"], cwd=tmp_path)

    assert (
        "myfile.py:3: error: assert_type failed. expected: 'builtins.float*', actual 'Literal[1]?"
        in exc_info.value.output
    )

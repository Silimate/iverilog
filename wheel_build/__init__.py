# Copyright (C) 2026 Silimate Inc.
#
# Written by Mohamed Gaber <me@donn.website>
#
# Adapted from Yosys
#
# Copyright (C) 2026 Catherine <whitequark@whitequark.org>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
import os
import pathlib
import re
import tarfile
import tempfile
import sysconfig
import subprocess
import hashlib
import urllib.request
from email.policy import EmailPolicy
from email.message import EmailMessage
from typing import Tuple, Iterable, Optional
from wheel.wheelfile import WheelFile
from packaging.version import parse as vparse

PROJECT_NAME = "iverilog"
PROJECT_VERSION = os.getenv(
    "IVERILOG_WHEEL_VERSION",
    subprocess.check_output(
        ["bash", "wheel_build/get_version.sh"],
        encoding="ascii",
    ),
)
DIST_NAME = f"{PROJECT_NAME}-{PROJECT_VERSION}"

PLATFORM_TAG_RAW = sysconfig.get_platform()
PLATFORM_TAG = (
    PLATFORM_TAG_RAW.lower().replace("-", "_").replace(".", "_").replace(" ", "_")
)
COMPAT_TAG = f"py3-none-{PLATFORM_TAG}"

# python uses ENTRY_POINTS in metadata to synthesize entries in ./venv/bin
ENTRY_POINTS = f"""
[console_scripts]
iverilog = {PROJECT_NAME}.__main__:iverilog
vvp = {PROJECT_NAME}.__main__:vvp
iverilog-vpi = {PROJECT_NAME}.__main__:iverilog_vpi
"""

# downloadable deps
AUTOCONF_URL = "https://ftp.gnu.org/gnu/autoconf/autoconf-2.73.tar.gz"
AUTOCONF_SHA256 = "259ddfa3bddc799cfb81489cc0f17dfdf1bd6d1505dda53c0f45ff60d6a4f9a7"


def build_sdist(sdist_dir, config_settings=None):
    sdist_filename = f"{DIST_NAME}.tar.gz"

    with tarfile.open(
        pathlib.Path(sdist_dir) / sdist_filename,
        "w:gz",
        format=tarfile.PAX_FORMAT,
    ) as sdist:

        def exclude_build(entry):
            name = os.path.basename(entry.name)
            if name in (
                ".git",
                ".github",
                ".cache",
                "build",
                "dist",
                "venv",
                ".venv",
                "test",
                "__pycache__",
            ):
                return
            if (
                name.endswith(".whl")
                or name.endswith(".tgz")
                or name.endswith(".tar.gz")
            ):
                return
            return entry

        sdist.add(os.getcwd(), arcname=DIST_NAME, filter=exclude_build)

    return sdist_filename


def make_message(headers: Iterable[Tuple[str, str]], payload: Optional[str] = None):
    """
    converts a set of python tuples and an optional payload in a manner
    consistent with
    https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata
    """
    msg = EmailMessage(policy=EmailPolicy(max_line_length=0))
    for name, value in headers:
        if isinstance(value, list):
            for value_part in value:
                msg[name] = value_part
        else:
            msg[name] = value
    if payload:
        msg.set_payload(payload)
    return bytes(msg)


def get_metadata_files():
    """
    (see https://packaging.python.org/en/latest/specifications/recording-installed-packages/)
    """
    with open("README.md", "rb") as readme:
        long_description = readme.read()

    return {
        "WHEEL": make_message(
            [
                ("Wheel-Version", "1.0"),
                ("Generator", "custom silimate iverilog build backend"),
                ("Root-Is-Purelib", "false"),
                ("Tag", [COMPAT_TAG]),
            ]
        ),
        "METADATA": make_message(
            [
                ("Metadata-Version", "2.4"),
                ("Name", PROJECT_NAME),
                ("Version", PROJECT_VERSION),
                (
                    "Summary",
                    "Superset of STA for operator resize for meeting timing",
                ),
                ("Description-Content-Type", "text/markdown"),
                ("Classifier", "Programming Language :: Python :: 3"),
                ("Requires-Python", ">=3.8"),
                ("License", "MIT"),
            ],
            long_description,
        ),
        "entry_points.txt": ENTRY_POINTS.encode("utf8"),
    }


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    """
    top-level function (called by pip during wheel build)

    generates dist-info
    """
    os.mkdir(f"{metadata_directory}/{DIST_NAME}.dist-info")

    for filename, contents in get_metadata_files().items():
        with open(f"{metadata_directory}/{DIST_NAME}.dist-info/{filename}", "wb") as f:
            f.write(contents)

    return f"{DIST_NAME}.dist-info"


def _ensure_autoconf_273(d):
    try:
        version_rx = re.compile(r"autoconf\s*\(.+\) (\d+\.\d+)")
        version_str = subprocess.check_output(
            ["autoconf", "--version"],
            encoding="utf8",
        )
        if match := version_rx.search(version_str):
            version = vparse(match[1])
            if version >= vparse("2.73"):
                return None
    except subprocess.CalledProcessError:
        pass

    urllib.request.urlretrieve(AUTOCONF_URL, d / "autoconf.tar.gz")
    with open(d / "autoconf.tar.gz", "rb") as f:
        buffer = f.read()
        sha256 = hashlib.sha256()
        sha256.update(buffer)
        got = sha256.hexdigest()
        if AUTOCONF_SHA256 != got:
            raise RuntimeError(f"upstream hash for autoconf source changed: {got}")

    with tarfile.open(d / "autoconf.tar.gz", mode="r:gz") as tf:
        tf.extractall(d / "autoconf-src")

    src_root = d / "autoconf-src" / "autoconf-2.73"

    subprocess.check_call(
        ["./configure", f"--prefix={d / 'autoconf'}"],
        cwd=src_root,
    )
    subprocess.check_call(
        ["make", f"-j{os.cpu_count()}"],
        cwd=src_root,
    )
    subprocess.check_call(
        ["make", "-j", "install"],
        cwd=src_root,
    )
    return d / "autoconf"


def build_wheel(wheel_dir, config_settings=None, metadata_directory=None):
    """
    top-level function (called by wheel build)

    builds iverilog and creates python version-agnostic wheel
    """
    wheel_filename = f"{DIST_NAME}-{COMPAT_TAG}.whl"

    with WheelFile(pathlib.Path(wheel_dir) / wheel_filename, "w") as wheel:
        # write metadata
        for filename, contents in get_metadata_files().items():
            wheel.writestr(f"{DIST_NAME}.dist-info/{filename}", contents)

        # build in temporary directory
        with tempfile.TemporaryDirectory(f".{PROJECT_NAME}-build", "w") as d_str:
            d = pathlib.Path(d_str)

            # copy python files
            wheel.write(
                "wheel_build/iverilog/__init__.py", f"{PROJECT_NAME}/__init__.py"
            )
            wheel.write(
                "wheel_build/iverilog/__main__.py", f"{PROJECT_NAME}/__main__.py"
            )

            env = os.environ.copy()
            if autoconf := _ensure_autoconf_273(d):
                env["PATH"] = f"{autoconf}/bin:{env['PATH']}"

            # configure
            subprocess.check_call(["autoreconf", "-vfi"], env=env)
            subprocess.check_call(["./configure", f"--prefix={d}"])

            # build
            subprocess.check_call(
                [
                    "make",
                    "install",
                    f"-j{os.cpu_count()}",
                ]
            )

            # copy the entire prefix
            for root, _, files in os.walk(d):
                for file in files:
                    resolved = os.path.join(root, file)
                    rel = os.path.relpath(resolved, d)
                    wheel.write(resolved, f"{PROJECT_NAME}/{rel}")

    return wheel_filename

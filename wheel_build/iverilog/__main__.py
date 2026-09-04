import os
import sys

from . import IVERILOG_BIN_PATH, IVERILOG_PREFIX


def iverilog():
    os.execl(IVERILOG_BIN_PATH, "iverilog", *sys.argv[1:])


def vvp():
    os.execl(IVERILOG_PREFIX / "bin" / "vvp", "vvp", *sys.argv[1:])


def iverilog_vpi():
    os.execl(IVERILOG_PREFIX / "bin" / "iverilog-vpi", "iverilog-vpi", *sys.argv[1:])


if __name__ == "__main__":
    iverilog()

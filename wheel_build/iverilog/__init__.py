from pathlib import Path

__file_dir__ = Path(__file__).absolute().parent
IVERILOG_BIN_PATH = binary_path = __file_dir__ / "bin" / "iverilog"
IVERILOG_PREFIX = __file_dir__

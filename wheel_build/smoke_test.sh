#!/usr/bin/env bash
set -xeuo pipefail
iverilog -o check.vvp examples/hello.vl
vvp check.vvp

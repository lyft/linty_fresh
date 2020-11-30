#!/bin/bash

set -euo pipefail
set -x

python setup.py test
pre-commit run -a

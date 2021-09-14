#!/bin/bash

set -euo pipefail

curl -H "Authorization: Bearer $GITHUB_AUTH_TOKEN" https://api.github.com/user

python setup.py test
pre-commit run -a

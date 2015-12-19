#!/bin/bash -x

set -e
python setup.py test

GITHUB_SLUG="$(git config --get remote.origin.url | \
  sed 's/git@github.com*:\([^\.]*\)\.git/\1/')"

# This is a bit of a hack.  Travis tests pushes to branches and pull
# requests.  Unfortunately, the pull request tests are testing the merge
# commit between the PR and master.  This is desirable for unit tests,
# but for lint it's less desirable due to line numbers not matching up.
if [ -n "${TRAVIS_PULL_REQUEST}" ] && \
   [ "${TRAVIS_PULL_REQUEST}" != 'false' ]; then
    git checkout HEAD^2
fi

COMMIT="$(git rev-parse HEAD)"

set +e
set -o pipefail

python setup.py flake8 |& tee flake8.txt
LINT_RESULT=$?

if [ -n "${TRAVIS_PULL_REQUEST}" ] && \
   [ "${TRAVIS_PULL_REQUEST}" != 'false' ] && \
   [ -n "${GITHUB_SLUG}" ] && \
   [ -n "${GITHUB_AUTH_TOKEN}" ]; then
    COMMIT="$(git rev-parse HEAD)"
    PR_URL="https://github.com/${GITHUB_SLUG}/pull/${TRAVIS_PULL_REQUEST}"
    linty_fresh --pr_url "${PR_URL}" --commit "${COMMIT}" \
                --linter pylint flake8.txt
fi

exit ${LINT_RESULT}

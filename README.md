:sparkles: Linty Fresh :sparkles: [![Build Status](https://travis-ci.org/lyft/linty_fresh.svg)](https://travis-ci.org/lyft/linty_fresh) [![Join the chat at https://gitter.im/lyft/linty_fresh](https://badges.gitter.im/lyft/linty_fresh.svg)](https://gitter.im/lyft/linty_fresh?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
===============================

Keep your codebase sparkly clean with the power of **LINT**!

Linty Fresh parses lint errors and report them back to GitHub as comments on a
pull request.

![Linty Fresh](http://i.imgur.com/epWogrw.png)


Requirements
------------
 - [Python 3](https://www.python.org/downloads/)

Contributing
------------
[CONTRIBUTING.md](CONTRIBUTING.md)

Installation
------------
Linty Fresh is hosted in [PyPi](https://pypi.python.org/pypi).  To get started,
Run

```shell
pip3 install linty-fresh
```

### Install from source

Linty Fresh uses setuptools for installation.  After cloning the repo, run

```shell
python3 setup.py install
```


Usage
-----

We recommend you create a GitHub user for your organization used just for
commenting on PRs.  [Create a token](https://github.com/settings/tokens/new)
for that user that only has access to the `repo` scope (or `public_repo` scope
for OSS projects).  Then add that token as a secret to your CI system as the
environment variable `GITHUB_AUTH_TOKEN`.  You should ensure this user and it's
token are scoped down as much as possible.  You should assume that anyone who
has permissions to run a job in your CI system would have access to this token.
See Travis CI documentation [storing encrypted secrets][] for more information.

If you are looking for a good secret management system to store secrets like
this, check out [Confidant](https://github.com/lyft/confidant/).

Once you have your GitHub user, integrating Linty Fresh is easy!  Assuming you
are running PyLint and the output is going to `pylint.txt`, add the following
snippet to the bottom of your automation script.

```bash
linty_fresh --pr_url ${PR_URL} --commit "${COMMIT}" \
            --linter pylint pylint.txt
```

Take a look at our [run_tests.sh](scripts/run_tests.sh) script as an example
for how this works on Travis CI.

Currently each invocation of linty_fresh can only accept one lint file, but
this will likely change.

Supported Linters
-----------------
- [Flake8](https://pypi.python.org/pypi/flake8)
- [Swiftlint](https://github.com/realm/SwiftLint)
- [Mypy](http://mypy-lang.org/)
- [Checkstyle](http://checkstyle.sourceforge.net/)
- [Android](https://developer.android.com/studio/write/lint.html)

[storing encrypted secrets]: https://docs.travis-ci.com/user/encryption-keys/

:sparkles: Contributing to Linty Fresh :sparkles:
=================================================

CLA
---
In order to clarify the intellectual property rights in the project, and to
grant licenses to the project to others, we require contributors accept the
CLA.  Don't worry, we don't need anything faxed in, just a PR from you.  Follow
the instructions at https://github.com/lyft/CLA and you'll be good to
contribute.

Python 3.5
----------
Linty Fresh is currently written to target Python 3.5, partly as a way to
experiment with [Type Hints](https://www.python.org/dev/peps/pep-0484/) and
[async/await](https://www.python.org/dev/peps/pep-0492/).  When possible, use
asynchronous libraries like [aiohttp](https://github.com/KeepSafe/aiohttp) or
 [asyncio](https://docs.python.org/3/library/asyncio.html).  Where appropriate,
 add type hints.  Unfortunately mypy, the type checker for PEP 0484 types,
 doesn't support parsing async/await code yet (see
 https://github.com/JukkaL/mypy/issues/913) so we can't integrate types into
 CI, but PyCharm is able to parse/validate types.

Running Tests
-------------
```py
python3 setup.py test
python3 setup.py flake8
```

Implementing a New Linter
-------------------------

Implementing a new linter is fairly straight forward.  Under the
[linters](linty_fresh/linters/) directory, add a new python file with the name 
of the linter you want to support.  This file should implement a function 
`parse` with the signature:

```py
def parse(contents: str) -> Set[Problem]:
```

It should take the contents of a lint file and return a set of
[Problems](linty_fresh/problem.py) for each problem parsed in that file.

Then, add an entry in the `LINTERS` map in [main.py](linty_fresh/main.py#L15)
for your new linter module.  You should now ne able to specify this linter as
one of the linters on the command line.

Before submitting a PR, please add unit tests.

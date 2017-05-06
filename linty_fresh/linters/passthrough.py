from typing import Set

from linty_fresh.problem import Problem


def parse(contents: str, **kwargs) -> Set[Problem]:
    if contents:
        return set([Problem('', 0, contents.strip())])
    else:
        return set()

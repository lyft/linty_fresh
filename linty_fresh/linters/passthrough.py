from typing import Set

from linty_fresh.problem import Problem


def parse(contents: str, **kwargs) -> Set[Problem]:
    return set(Problem('', 0, x) for x in contents.splitlines())

#!/usr/bin/env python

"""Validate and merge all our requirements.txt files into a single requirements file.
Checks performed:
  - (Warning) package version is not pinned
  - (Fatal) package is duplicated with different versions
  - (Fatal) specific app requirements missing from main file

This script is based on:
`find surface/ -name requirements*.txt -type f -exec cat {} + | grep -v '^-r ' | grep -v '^#' | sort | uniq > docker/requirements_full.txt`

Example of the new main function (useful for doctest)
>>> main(Path('testdata/requirements.txt'))
docker[oth,other,tls]==4.1.0
0
"""

import sys
from pathlib import Path

from pip._internal.req import parse_requirements
from pip._internal.req.constructors import (
    InstallRequirement,
    install_req_from_parsed_requirement,
)
from pip._internal.req.req_file import ParsedRequirement


def main(initial_req: Path):
    subdir_requirements = set(
        map(str, initial_req.parent.glob("**/*/requirements*.txt"))
    )
    imported_requirements = set(
        str(initial_req.parent.joinpath(r.strip().replace("-r ", "")))
        for r in initial_req.open("r")
        if r.startswith("-r ")
    )

    diff = subdir_requirements - imported_requirements
    if diff:
        print(f'[Fatal] {diff} are missing from {initial_req}', file=sys.stderr)
        return 1

    ss = set()
    for f in initial_req.parent.glob("**/requirements*.txt"):
        ss.update(
            {
                install_req_from_parsed_requirement(req)
                for req in parse_requirements(str(f), session='reqs')
            }
        )

    requirements = {}
    for item in ss:
        if not isinstance(item, InstallRequirement):
            continue

        if not item.match_markers():
            continue

        if not item.req.specifier:
            print(
                f'[Warning] {item} is not pinned to (a) specific version(s)',
                file=sys.stderr,
            )

        if requirements.get(item.name, item).req.specifier != item.req.specifier:
            print(
                f'[Fatal] {item.name} is duplicated with different versions: {item.req.specifier} vs {requirements[item.name].req.specifier}',
                file=sys.stderr,
            )

            return 1

        if item.name in requirements:
            requirements[item.name].req.extras.update(item.req.extras)
        else:
            requirements[item.name] = item

    reqs = []
    for _, item in requirements.items():
        if item.link:
            reqs.append(str(item.link.url))
        else:
            reqs.append(str(item.req))

    for req in sorted(reqs):
        print(req)

    return 0


if __name__ == '__main__':
    sys.exit(main(Path(sys.argv[1])))

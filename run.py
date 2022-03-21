#!/usr/bin/env python

"""Validate and merge all our requirements.txt files into a single requirements file.
Checks performed:
  - (Warning) package version is not pinned
  - (Fatal) package is duplicated with different versions
  - (Fatal) specific app requirements missing from main file

This script is based on:
`find surface/ -name requirements*.txt -type f -exec cat {} + | grep -v '^-r ' | grep -v '^#' | sort | uniq > docker/requirements_full.txt`

Example of the new main function (useful for doctest)
>>> main(['testdata/requirements-1.txt'])
docker[oth,other,tls]==4.1.0
0
>>> main(['testdata/requirements-2.txt'])
flake8==4.0.1
requests==2.27.1
0
>>> main(['testdata/requirements-1.txt', 'testdata/requirements-2.txt'])
docker[oth,other,tls]==4.1.0
flake8==4.0.1
requests==2.27.1
0
>>> main(['testdata/requirements-3.txt'])
requests
0
>>> main(['testdata/requirements-4.txt'])
1
"""

import argparse
import logging
from pathlib import Path

from pip._internal.req import parse_requirements
from pip._internal.req.constructors import (
    InstallRequirement,
    install_req_from_parsed_requirement,
)

logger = logging.getLogger(__name__)


def build_parser():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "files",
        metavar="FILE",
        type=Path,
        nargs="+",
        help="path to requirements.txt-like file",
    )
    parser.add_argument("--debug", "-d", action="store_true", help="debug verbosity")
    return parser


def main(argv=None):
    logging.basicConfig()
    args = build_parser().parse_args(argv)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("debug enabled")

    imported_requirements = set(map(str, args.files))

    for initial_req in args.files:
        with initial_req.open("r") as inf:
            imported_requirements.update(
                str(initial_req.parent.joinpath(r.strip()[3:]))
                for r in inf
                if r.startswith("-r ")
            )

    logger.debug(f'files to process: {", ".join(imported_requirements)}')

    ss = set()
    for f in imported_requirements:
        ss.update(
            {
                install_req_from_parsed_requirement(req)
                for req in parse_requirements(str(f), session="reqs")
            }
        )

    requirements = {}
    for item in ss:
        if not isinstance(item, InstallRequirement):
            continue

        if not item.match_markers():
            continue

        if not item.req.specifier:
            logger.warning(f"{item} is not pinned to (a) specific version(s)")

        if requirements.get(item.name, item).req.specifier != item.req.specifier:
            logger.fatal(
                f"{item.name} is duplicated with different versions: {item.req.specifier} vs {requirements[item.name].req.specifier}"
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


if __name__ == "__main__":
    exit(main())

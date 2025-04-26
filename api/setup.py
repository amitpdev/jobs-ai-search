import os
import pathlib
import re

import pkg_resources
from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

init_raw = open(os.path.join(ROOT, "src/__init__.py")).read()
metadata = dict(re.findall(r'__([a-z]+)__ = "([^"]*)"', init_raw))


def read_requires(filename):
    with pathlib.Path(filename).open() as requirements_txt:
        return [
            str(requirement)
            for requirement in pkg_resources.parse_requirements(
                requirements_txt
            )
        ]


setup(
    name="linked-api",
    version=metadata["version"],
    description=metadata["doc"],
    long_description=metadata["doc"],
    author=metadata["author"],
    author_email=metadata["email"],
    license=metadata["license"],
    url=metadata["url"],
    keywords="",
    packages=find_packages(),
    # package_data={
    #     '': ['*.txt', '*.md', '*.ini'],
    # },
    python_requires=">=3.11",
    include_package_data=True,
    install_requires=read_requires("requirements.txt"),
    extras_require={
        "test": read_requires("requirements-dev.txt"),
    },
    platforms="any",
    zip_safe=False,
    # entry_points={"console_scripts": ["linked-api = src.cli:cli"]},
)

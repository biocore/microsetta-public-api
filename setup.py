# ----------------------------------------------------------------------------
# Copyright (c) 2019-, The Microsetta Initiative development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from setuptools import setup, find_packages

import versioneer

setup(
    name="microsetta-public-api",
    packages=find_packages(),
    version=versioneer.get_version(),
    url="https://github.com/biocore/microsetta-public-api",
    description="A RESTful API to support The Microsetta Initiative",
    license='BSD-3-Clause',
    install_requires=[
        'connexion[swagger-ui]',
        'flask',
        'pyyaml',
        'pandas',
        'numpy',
        'biom-format>=2.0',
        'scikit-bio',
        'altair',
    ],
    extras_require={
        "dev": [
            "pytest",
            "flake8",
        ]
    },
)

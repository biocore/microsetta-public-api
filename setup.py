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
    cmdclass=versioneer.get_cmdclass(),
    url="https://github.com/biocore/microsetta-public-api",
    description="A RESTful API to support The Microsetta Initiative",
    license='BSD-3-Clause',
    install_requires=[
        'connexion[swagger-ui]',
        'flask',
        'flask-cors',
        'pyyaml',
        'pandas',
        'numpy',
        'biom-format>=2.0',
        'scikit-bio',
        'altair',
        'jsonschema',
        'empress>=1.0.1',
    ],
    package_data={'microsetta_public_api':
                  [
                     'api/microsetta_public_api.yml',
                     'server_config.json'
                  ]},
)

import os
import json
from microsetta_public_api.exceptions import ConfigurationError

# NOTE: importlib replaces setuptools' pkg_resources as of Python 3.7
# See: https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package # noqa

PACKAGE_NAME = __name__.split('.')[0]
CONFIG_FILE = os.getenv("MPUBAPI_CFG", "server_config.json")

try:
    import importlib.resources as pkg_resources
    with pkg_resources.open_text(PACKAGE_NAME, CONFIG_FILE) as fp:
        SERVER_CONFIG = json.load(fp)

except ImportError:
    import pkg_resources
    content = pkg_resources.resource_string(PACKAGE_NAME, CONFIG_FILE)
    SERVER_CONFIG = json.loads(content)


class ResourcesConfig(dict):

    resource_fields = ['alpha_resources']

    def update(self, _m, **kwargs):

        for resource_field in self.resource_fields:
            if resource_field in _m:
                self._validate_resource_locations(_m[resource_field])

        return super().update(_m, **kwargs)

    @staticmethod
    def _validate_resource_locations(resource_locations):
        if not isinstance(resource_locations, dict):
            raise ConfigurationError('resource_locations must be '
                                     'able to be parsed into a python '
                                     'dictionary.')
        all_keys_str = all(isinstance(key, str) for key in
                           resource_locations)
        if not all_keys_str:
            raise ConfigurationError('All `alpha_resources` keys must be '
                                     'strings.')
        all_values_fp = all(os.path.exists(val) for val in
                            resource_locations.values())
        if not all_values_fp:
            raise ConfigurationError('All `alpha_resources` values must be '
                                     'existing file paths.')
        return True


resources = ResourcesConfig()

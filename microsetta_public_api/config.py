import os
import json
from typing import Union
import jsonschema

from microsetta_public_api.backend import constructors
from microsetta_public_api.exceptions import ConfigurationError


class ResourcesConfigEntry(dict):

    def __init__(self, name, components=None, construct=None, config=None):
        super().__init__()
        internal = dict()
        if components:
            internal['components'] = components
        if construct:
            internal['construct'] = construct
        if config:
            internal['config'] = config
        entry = {name: internal}
        self.update(entry)


def component_schema(properties=None,
                     required=None,
                     named_components: Union[dict, bool] = False,
                     construct=False,
                     config=False,
                     components=False,
                     additional_properties=False,
                     ):
    if properties is None:
        properties = {}
    required_parts = [element for element, is_required in
                      zip(['construct', 'config', 'components'],
                          [construct, config, components])
                      if is_required
                      ]
    return {
        "type": "object",
        "properties": {
            "components": {
                "type": "object",
                "properties": properties,
                "required": required if required
                else list(),
                "additionalProperties": named_components,
            },
            "config": {
                "type": "object",
            },
            "construct": {
                "type": "string",
                "enum": list(constructors.keys()),
            },
        },
        "required": required_parts,
        "additionalProperties": additional_properties
    }


general_schema = {
    "type": "object",
    "additionalProperties":
        {
            "type": "object",
            "properties": {
                "components": {
                    "type": "object",
                    "schema": {
                        # the items in components should match this schema (
                        # recursive)
                        "$ref": '#',
                    }
                },
                "config": {
                    "type": "object",
                },
                "construct": {
                    "type": "string",
                    "enum": list(constructors.keys()),
                },
            }
        }
}


schema = {
    "type": "object",
    "properties": {
        "datasets": component_schema(
            properties={
                "metadata": component_schema(construct=True),
            },
            # This named_components portion implicitly allows arbitrarily
            # named datasets
            named_components=component_schema(
                {
                    "alpha_diversity": component_schema(
                        named_components=component_schema(
                            construct=True,
                        )
                    ),
                    "taxonomy": component_schema(
                        named_components=component_schema(
                            properties={
                                "taxonomy": component_schema(
                                    construct=True),
                                "table": component_schema(construct=True),
                            },
                            required=['taxonomy', 'table'],
                        )
                    ),
                    "pcoa": component_schema(
                        named_components=component_schema(
                            named_components=component_schema(
                                construct=True,
                            )
                        )
                    )
                }, additional_properties=False,
            )
        )
    }
}


def validate(resources_config):
    jsonschema.validate(instance=resources_config, schema=schema)


# NOTE: importlib replaces setuptools' pkg_resources as of Python 3.7
# See: https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package # noqa

PACKAGE_NAME = __name__.split('.')[0]
CONFIG_FILE = os.getenv("MPUBAPI_CFG", "server_config.json")

try:
    import importlib.resources as pkg_resources
    with pkg_resources.open_text(PACKAGE_NAME, CONFIG_FILE) as fp:
        SERVER_CONFIG = json.load(fp)
    validate(SERVER_CONFIG['resources'])

except ImportError:
    import pkg_resources
    content = pkg_resources.resource_string(PACKAGE_NAME, CONFIG_FILE)
    SERVER_CONFIG = json.loads(content)
    validate(SERVER_CONFIG['resources'])


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

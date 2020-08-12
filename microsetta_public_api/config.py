import os
import json
from typing import Union
import jsonschema

from microsetta_public_api.backend import constructors


def component_schema(properties=None,
                     required=None,
                     named_components: Union[dict, bool] = False,
                     construct=False,
                     config=False,
                     components=False,
                     additional_properties=False,
                     ):
    """
    Helper for defining a schema composed of a hierarchy of components

    Parameters
    ----------
    properties : dict, optional
        A dict of specifically named sub-components with schemas.
    required : list, optional
        Allows you to specify required sub-components of this component.
    named_components : bool or dict, optional
        False if no sub-components with arbitrary names should be allowed.
        True, otherwise. Can also use a dictionary to specify the expected
        schema of the sub-components.
    construct : bool, optional
        Indicates wheterh `construct` should be a requiref field for this
        component. Default: False
    config : bool, optional
        Indicates whether `config` should be a required field for this
        component. Default: False
    components : bool, optional
        Indicates whether `components` should be a required field for this
        component. Default: False
    additional_properties : bool, optional
        Indicates whether properties in addition to `construct`,
        `config`, or `components` should be allowed. Default: False

    Returns
    -------
    dict
        The output schema

    """
    if properties is None:
        properties = {}
    required_parts = [element for element, is_required in
                      zip(['construct', 'config', 'components'],
                          [construct, config, components])
                      if is_required
                      ]
    component = {
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
    return component


# This general schema defines a general configuration structure that can be
# parsed by microsetta_public_api.resources_alt.Component.
# It allows for arbitrarily named entries (additionalProperties) that may
# contain the following fields:
# 1. components : an object that contains sub-components, which share the
#     same form as the overall schema
# 2. construct : an enum that determines the class that specifies how this
#     component should be constructed.
# 3. config : an object that is passed as kwargs to the class specified by
#     `construct`. Can be used to, for example specify a file to load,
#     but could also forseeably specify the arguments for establishing a
#     database connection
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
                "construct": {
                    "type": "string",
                    "enum": list(constructors.keys()),
                },
                "config": {
                    "type": "object",
                },
            }
        }
}


# This a more specific version of general_schema, that specifically outlines
# where we expect to see certain data types, such as alpha diversity, metadata,
# taxonomy, etc. This is should be cohesive with `general_schema` and is
# also parsable by microsetta_public_api.resources_alt.Component.
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
    },
    # for now, additionalProperties is True for backward compatibility,
    # but once everything is converted, we may want to switch this to False
    "additionalProperties": True,
}


class Entry(dict):
    """
    Helper class for constructing configs that match the schemas here

    Examples
    --------
    >>> Entry(
    ...     'resources',
    ...     components=Entry('datasets', components={
    ...         **Entry('metadata',
    ...                 construct='MetadataLoader',
    ...                 config={'file': '/path/to/metadata.tsv'},
    ...                 ),
    ...         **Entry(
    ...             '16SAmplicon',
    ...             components={
    ...                 **Entry(
    ...                     'alpha_diversity',
    ...                     components={
    ...                         **Entry('faith_pd',
    ...                                 construct='AlphaQZALoader',
    ...                                 config={'file': '/path/to/alpha1.qza'},
    ...                                 ),
    ...                         **Entry('shannon',
    ...                                 construct='AlphaQZALoader',
    ...                                 config={'file': '/path/to/alpha1.qza'},
    ...                                 ),
    ...                     }),
    ...                 **Entry(
    ...                     'pcoa',
    ...                     components={
    ...                         **Entry(
    ...                             'oral',
    ...                             components={
    ...                                 **Entry(
    ...                                     'unifrac',
    ...                                     construct='PCOALoader',
    ...                                     config={'file':
    ...                                               '/path/to/oral-'
    ...                                               'unifrac.qza'},
    ...                                 ),
    ...                             }
    ...                         )
    ...                     }
    ...                 )
    ...             }
    ...         )
    ...     })
    ... )
    >>>
    """

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


resources = dict()

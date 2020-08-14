import os
import json
from typing import Union
import jsonschema

from abc import abstractmethod

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


alpha_schema = {
    "type": "string",
    "description":
        "Filepath to an alpha diversity "
        "QZA"
}

alpha_group_schema = {
    "type": "object",
    "additionalProperties": alpha_schema,
    "description": "A group of related alpha diversity objects.",
}

taxonomy_schema = {
    "type": "object",
    "properties": {
        "table": {
            "type": "string",
            "description": "Path to a FeatureTable QZA with features indexed "
                           "on taxonomy",
        },
        "feature-data-taxonomy": {
            "type": "string",
            "description": "Path to a FeatureData[Taxonomy] QZA",
        },
    },
    "required": ["table", "feature-data-taxonomy"],
}


taxonomy_group_schema = {
    "type": "object",
    "additionalProperties": taxonomy_schema,
    "description": "A group of related taxonomies."
}


pcoa_schema = {
    "type": "object",
    "additionalProperties":
        {
            "type": "string",
            "description": "Path to a PCOA QZA",
        },
}


pcoa_group_schema = {
    "type": "object",
    "additionalProperties": pcoa_schema,
    "description": "A group of related PCOAs.",
}


metadata_schema = {
    "type": "string",
    "description": "A filepath to the metadata file.",
}


def alpha_kw():
    return "__alpha__"


def taxonomy_kw():
    return "__taxonomy__"


def pcoa_kw():
    return "__pcoa__"


def metadata_kw():
    return "__metadata__"


def schema_alt():
    return {
        "type": "object",
        "properties": {
            "datasets":
                {
                    "type": "object",
                    "properties": {
                        metadata_kw(): metadata_schema,
                    },
                    "additionalProperties":
                        {
                            "type": "object",
                            "properties": {
                                alpha_kw(): alpha_group_schema,
                                taxonomy_kw(): taxonomy_group_schema,
                                pcoa_kw(): pcoa_group_schema,
                            },
                            "additionalProperties": False,
                        }
                }
        },
    }


class Element:

    # need args and kwargs for inheritance concerns
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.data = None

    @abstractmethod
    def accept(self, visitor):
        raise NotImplementedError()

    def gets(self, *args):
        """

        Parameters
        ----------
        *args
            A path of keys

        Returns
        -------
        object
            The object located by the path of keys


        Raises
        ------
        KeyError
            There is no element with the given path of keys

        Examples
        --------
        >>> s = create_literal_element('baz')
        >>> qux = DictElement({'foo': DictElement({'bar': s('baz')})})
        >>> qux.gets('foo', 'bar')
        baz
        >>> qux.gets('foo')
        {'bar': 'baz'}

        """
        if len(args) == 0:
            return self
        first = args[0]
        rest = args[1:]
        try:
            child = self[first]
        # if you can't index into self for whatever reason, give me a key error
        except (TypeError, KeyError, IndexError):
            raise KeyError(first)
        return child.gets(*rest)

    def has(self, *args):
        """

        Parameters
        ----------
        *args
            A path of keys

        Returns
        -------
        bool
           Indicates whether the path of keys exists in the Element


        Examples
        --------
        >>> s = create_literal_element('baz')
        >>> qux = DictElement({'foo': DictElement({'bar': s('baz')})})
        >>> qux.has('foo', 'bar')
        True
        >>> qux.gets('foo')
        True
        >>> qux.gets('foo', 'corge')
        False

        """
        if len(args) == 0:
            return True
        first = args[0]
        rest = args[1:]
        try:
            next_ = self[first]
            return next_.has(*rest)
        # if you can't index into self for whatever reason, it doesn't exist!
        except (TypeError, KeyError, IndexError):
            return False


class DictElement(dict, Element):

    # def _get(self, item):
    #     return super(DictElement, self).__getitem__(item)
    #
    # def __getitem__(self, item):
    #     data = self._get(item)
    #     object_data = None
    #     try:
    #         object_data = data.data
    #     except AttributeError:
    #         pass
    #     if object_data is not None:
    #         data = object_data
    #
    #     return data
    #
    # def gets(self, *args):
    #     if len(args) == 0:
    #         return self
    #     first = args[0]
    #     rest = args[1:]
    #     try:
    #         child = self._get(first)
    #     # if you can't index into self for whatever reason, give me a key error
    #     except (TypeError, KeyError, IndexError):
    #         raise KeyError(first)
    #     return child.gets(*rest)

    def accept(self, visitor):
        for val in self.values():
            try:
                val.accept(visitor)
            # if val does not have an accept, do not accept on it
            # good for if the entries of the dict are bool or None, or have
            # not been converted to an Element
            except AttributeError:
                pass


class ListElement(list, Element):
    def accept(self, visitor):
        for val in self:
            try:
                val.accept(visitor)
            # if val does not have an accept, do not accept on it
            # good for if the entries of the list are bool or None, or have
            # not been converted to an Element
            except AttributeError:
                pass


class AlphaElement(DictElement):
    def accept(self, visitor):
        super().accept(visitor)
        visitor.visit_alpha(self)


class TaxonomyElement(DictElement):
    def accept(self, visitor):
        super().accept(visitor)
        visitor.visit_taxonomy(self)


class PCOAElement(DictElement):
    def accept(self, visitor):
        super().accept(visitor)
        visitor.visit_pcoa(self)


class MetadataElement(str, Element):

    def accept(self, visitor):
        visitor.visit_metadata(self)


class ConfigElementVisitor:

    @abstractmethod
    def visit_alpha(self, element):
        raise NotImplementedError()

    @abstractmethod
    def visit_taxonomy(self, element):
        raise NotImplementedError()

    @abstractmethod
    def visit_pcoa(self, element):
        raise NotImplementedError()

    @abstractmethod
    def visit_metadata(self, element):
        raise NotImplementedError()


class SchemaBase:
    def __init__(self):
        self.alpha_kw = '__alpha__'
        self.taxonomy_kw = '__taxonomy__'
        self.pcoa_kw = '__pcoa__'
        self.metadata_kw = '__metadata__'

    def element_map(self):
        map_ = {
            self.alpha_kw: AlphaElement,
            self.taxonomy_kw: TaxonomyElement,
            self.pcoa_kw: PCOAElement,
            self.metadata_kw: MetadataElement,
        }
        return map_

    @abstractmethod
    def schema(self):
        raise NotImplementedError()

    def validate(self, instance):
        return jsonschema.validate(instance=instance, schema=self.schema())

    def make_elements(self, json_dump):
        if isinstance(json_dump, list):
            for i, entry in enumerate(json_dump):
                json_dump[i] = self.make_elements(entry)
        elif isinstance(json_dump, dict):
            for key, value in json_dump.items():
                json_dump[key] = self.make_elements(value)
                element_type = self.element_map().get(key, False)
                if element_type:
                    json_dump[key] = element_type(self.make_elements(value))

        return ElementFactory.get_element(json_dump)


class Schema(SchemaBase):
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "datasets":
                    {
                        "type": "object",
                        "properties": {
                            self.metadata_kw: metadata_schema,
                        },
                        "additionalProperties":
                            {
                                "type": "object",
                                "properties": {
                                    self.alpha_kw: alpha_group_schema,
                                    self.taxonomy_kw: taxonomy_group_schema,
                                    self.pcoa_kw: pcoa_group_schema,
                                },
                                "additionalProperties": False,
                            }
                    },
            },
        }


class LegacySchema(SchemaBase):
    def __init__(self):
        self.alpha_kw = 'alpha_resources'
        self.taxonomy_kw = 'table_resources'
        self.pcoa_kw = 'pcoa'
        self.metadata_kw = 'metadata'

    def schema(self):
        return {
            "type": "object",
            "properties": {
                self.alpha_kw: alpha_group_schema,
                self.taxonomy_kw: taxonomy_group_schema,
                self.pcoa_kw: pcoa_group_schema,
                self.metadata_kw: metadata_schema,
            }
        }


class CompatibilitySchema(SchemaBase):
    def __init__(self):
        self.old_alpha_kw = 'alpha_resources'
        self.old_taxonomy_kw = 'table_resources'
        self.old_pcoa_kw = 'pcoa'
        self.old_metadata_kw = 'metadata'
        self.new_alpha_kw = '__alpha__'
        self.new_taxonomy_kw = '__taxonomy__'
        self.new_pcoa_kw = '__pcoa__'
        self.new_metadata_kw = '__metadata__'

    def element_map(self):
        return {
            self.old_alpha_kw: AlphaElement,
            self.old_taxonomy_kw: TaxonomyElement,
            self.old_pcoa_kw: PCOAElement,
            self.old_metadata_kw: MetadataElement,
            self.new_alpha_kw: AlphaElement,
            self.new_taxonomy_kw: TaxonomyElement,
            self.new_pcoa_kw: PCOAElement,
            self.new_metadata_kw: MetadataElement,
        }

    def schema(self):
        return {
            "type": "object",
            "properties": {
                self.old_alpha_kw: alpha_group_schema,
                self.old_taxonomy_kw: taxonomy_group_schema,
                self.old_pcoa_kw: pcoa_group_schema,
                self.old_metadata_kw: metadata_schema,
                "datasets":
                    {
                        "type": "object",
                        "properties": {
                            self.new_metadata_kw: metadata_schema,
                        },
                        "additionalProperties":
                            {
                                "type": "object",
                                "properties": {
                                    self.new_alpha_kw: alpha_group_schema,
                                    self.new_taxonomy_kw:
                                        taxonomy_group_schema,
                                    self.new_pcoa_kw: pcoa_group_schema,
                                },
                                "additionalProperties": False,
                            }
                    },
            }
        }


elements = {
    alpha_kw(): AlphaElement,
    taxonomy_kw(): TaxonomyElement,
    pcoa_kw(): PCOAElement,
    metadata_kw(): MetadataElement,
}


def create_literal_element(literal):
    class LiteralElement(Element, literal):
        def accept(self, visitor):
            pass
    return LiteralElement


class ElementFactory:

    @staticmethod
    def get_element(obj):
        if obj is None:
            return None
        if isinstance(obj, bool):
            return obj
        if isinstance(obj, int):
            return create_literal_element(int)(obj)
        if isinstance(obj, float):
            return create_literal_element(float)(obj)
        if isinstance(obj, str):
            return create_literal_element(str)(obj)
        if isinstance(obj, list):
            return ListElement(obj)
        if isinstance(obj, dict):
            return DictElement(obj)

        raise NotImplementedError(f"No Element for type: {type(obj)}")


def make_elements(json_dump, element_map=None):
    if element_map is None:
        element_map = elements
    if isinstance(json_dump, list):
        for i, entry in enumerate(json_dump):
            json_dump[i] = make_elements(entry, element_map=element_map)
    elif isinstance(json_dump, dict):
        for key, value in json_dump.items():
            json_dump[key] = make_elements(value, element_map=element_map)
            element_type = element_map.get(key, False)
            if element_type:
                json_dump[key] = element_type(
                    make_elements(value, element_map=element_map))

    return ElementFactory.get_element(json_dump)


# This a more specific version of general_schema, that specifically outlines
# where we expect to see certain data types, such as alpha diversity, metadata,
# taxonomy, etc. This is should be cohesive with `general_schema` and is
# also parsable by microsetta_public_api.resources_alt.Component.
# schema = {
#     "type": "object",
#     "properties": {
#         "datasets": component_schema(
#             properties={
#                 "metadata": component_schema(construct=True),
#             },
#             # This named_components portion implicitly allows arbitrarily
#             # named datasets
#             named_components=component_schema(
#                 {
#                     "alpha_diversity": component_schema(
#                         named_components=component_schema(
#                             construct=True,
#                         )
#                     ),
#                     "taxonomy": component_schema(
#                         named_components=component_schema(
#                             properties={
#                                 "taxonomy": component_schema(
#                                     construct=True),
#                                 "table": component_schema(construct=True),
#                             },
#                             required=['taxonomy', 'table'],
#                         )
#                     ),
#                     "pcoa": component_schema(
#                         named_components=component_schema(
#                             named_components=component_schema(
#                                 construct=True,
#                             )
#                         )
#                     )
#                 }, additional_properties=False,
#             )
#         )
#     },
#     # for now, additionalProperties is True for backward compatibility,
#     # but once everything is converted, we may want to switch this to False
#     "additionalProperties": True,
# }


class Entry(dict):
    """
    Helper class for constructing configs that match the schemas here

    Examples
    --------
    >>> resource_config = Entry('datasets', components={
    ...    **Entry('metadata',
    ...            construct='MetadataLoader',
    ...            config={'file': '/path/to/metadata.tsv'},
    ...            ),
    ...    **Entry(
    ...        '16SAmplicon',
    ...        components={
    ...            **Entry(
    ...                'alpha_diversity',
    ...                components={
    ...                    **Entry('faith_pd',
    ...                            construct='AlphaQZALoader',
    ...                            config={'file': '/path/to/alpha1.qza'},
    ...                            ),
    ...                    **Entry('shannon',
    ...                            construct='AlphaQZALoader',
    ...                            config={'file': '/path/to/alpha1.qza'},
    ...                            ),
    ...                }),
    ...            **Entry(
    ...                'pcoa',
    ...                components=Entry(
    ...                     'oral',
    ...                     components=Entry(
    ...                         'unifrac',
    ...                         construct='PCOALoader',
    ...                         config={'file': '/path/to/oral-unifrac.qza'},
    ...                     )))})})
    >>> json.dump({
    ...     "debug": true,
    ...     "port": 8084,
    ...     "use_test_database": false,
    ...     "resources": resource_config
    ... }, open('server_config.json', 'r'))
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

# ultimately change this to Schema once everything is converted
schema = CompatibilitySchema()

try:
    import importlib.resources as pkg_resources
    with pkg_resources.open_text(PACKAGE_NAME, CONFIG_FILE) as fp:
        SERVER_CONFIG = json.load(fp)
    schema.validate(SERVER_CONFIG['resources'])

except ImportError:
    import pkg_resources
    content = pkg_resources.resource_string(PACKAGE_NAME, CONFIG_FILE)
    SERVER_CONFIG = json.loads(content)
    schema.validate(SERVER_CONFIG['resources'])


resources = dict()

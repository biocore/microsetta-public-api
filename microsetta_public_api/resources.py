import os
import pandas as pd
import biom
from copy import deepcopy
from microsetta_public_api.exceptions import ConfigurationError
from qiime2 import Artifact
from q2_types.sample_data import AlphaDiversity, SampleData
from q2_types.feature_table import FeatureTable, Frequency
from q2_types.feature_data import FeatureData, Taxonomy


def _dict_of_paths_to_alpha_data(dict_of_qza_paths, resource_name):
    _validate_dict_of_qza_paths(dict_of_qza_paths,
                                resource_name)
    new_resource = _replace_paths_with_qza(dict_of_qza_paths,
                                           SampleData[AlphaDiversity],
                                           view_type=pd.Series)
    return new_resource


def _transform_dict_of_table(dict_, resource_name):
    if not isinstance(dict_, dict):
        raise TypeError(f"Expected field '{resource_name}' to contain a "
                        f"dictionary. Got {dict_}.")
    new_resource = dict()
    for table_name, attributes in dict_.items():
        res = _transform_single_table(attributes, table_name)
        new_resource[table_name] = res
    return new_resource


def _transform_single_table(dict_, resource_name):
    _validate_dict_of_qza_paths(dict_, resource_name, allow_none=True,
                                required_fields=['table'],
                                non_qza_entries=['table-type'],
                                allow_extras=True,
                                )
    semantic_types = {
        'table': dict_.get('table-type', FeatureTable[Frequency]),
        'feature-data-taxonomy': FeatureData[Taxonomy],
        'variances': FeatureTable[Frequency],
    }
    views = {
        'table': biom.Table,
        'feature-data-taxonomy': pd.DataFrame,
        'variances': biom.Table,
    }
    new_resource = deepcopy(dict_)
    for key, value in dict_.items():
        if key in semantic_types:
            new_resource[key] = _parse_q2_data(value,
                                               semantic_types[key],
                                               view_type=views.get(key, None),
                                               )
    return new_resource


def _parse_q2_data(filepath, semantic_type, view_type=None):
    try:
        data = Artifact.load(filepath)
    except ValueError as e:
        raise ConfigurationError(*e.args)

    if data.type != semantic_type:
        raise ConfigurationError(f"Expected QZA '{filepath}' to have type "
                                 f"'{semantic_type}'. "
                                 f"Received '{data.type}'.")
    if view_type is not None:
        data = data.view(view_type=view_type)

    return data


def _validate_dict_of_qza_paths(dict_of_qza_paths, name, allow_none=False,
                                required_fields=None, allow_extras=False,
                                non_qza_entries=None,
                                ):
    if non_qza_entries is None:
        non_qza_entries = []
    if not isinstance(dict_of_qza_paths, dict):
        raise ValueError(f"Expected '{name}' field to contain a dict. "
                         f"Got {type(dict_of_qza_paths).__name__}")
    if required_fields:
        for field in required_fields:
            if field not in dict_of_qza_paths:
                raise ValueError(f"Did not get required field '{field}'.")
        if not allow_extras:
            allowed_keys = set(required_fields) | set(non_qza_entries)
            extra_keys = list(filter(lambda x: x not in allowed_keys,
                                     dict_of_qza_paths.keys()))
            if extra_keys:
                raise ValueError(f"Extra keys: {extra_keys} not allowed.")

    for key, value in dict_of_qza_paths.items():
        if key in non_qza_entries:
            continue
        is_qza = isinstance(value, str) and (value.endswith('.qza'))
        exists = isinstance(value, str) and os.path.exists(value)
        is_none = value is None
        value_is_existing_qza_path = (is_qza and exists) or \
                                     (is_none and allow_none)

        if not value_is_existing_qza_path:
            raise ValueError('Expected existing path with .qza '
                             'extension. Got: {}'.format(value))


def _replace_paths_with_qza(dict_of_qza_paths, semantic_type, view_type=None):
    new_resource = dict()
    for key, value in dict_of_qza_paths.items():
        new_resource[key] = _parse_q2_data(value,
                                           semantic_type,
                                           view_type=view_type,
                                           )
    return new_resource


class ResourceManager(dict):

    transformers = {
        'alpha_resources': _dict_of_paths_to_alpha_data,
        'table_resources': _transform_dict_of_table,
    }

    def update(self, *args, **kwargs):
        """
        Updates the managers resources.

        Parameters
        ----------
        other : optional dict
            Resource identifier to resource mapping. 'alpha_resources' is
            reserved for a dictionary. The values in 'alpha_resources' must be
            existing file paths with a .qza extension, they will be read
            into a python QZA.
        kwargs : dict
            kwargs for dict.update. Similar to `other`, but can be passed as
            keywords.

        Returns
        -------
        NoneType

        Examples
        --------
        >>> resources = ResourceManager(
        ...     alpha_resources={
        ...         'faith_pd': '/path/to/some.qza',
        ...         'chao1': '/another/path/to/a.qza',
        ...     },
        ...     table_resources={
        ...         'greengenes_13.8_insertion': {
        ...             'table': '/path/to/feature-table.qza',
        ...             'feature-data-taxonomy': '/a/feat-data-taxonomy.qza',
        ...             'variances': '/a/variance/feature-table.qza',
        ...         },
        ...         'some_other_feature_table': {
        ...             'table': '/another/path/tofeature-table.qza',
        ...             'variances': '/a/variance/feature-table.qza',
        ...             'table-type': FeatureTable[Frequency],
        ...         },
        ...     }
        ...     some_other_resource='here is a string resource',
        ...     )

        """
        if len(args) == 1 and isinstance(args[0], dict):
            other = args[0]
        elif len(args) == 0:
            other = dict()
        else:
            raise TypeError(f'update expected at most 1 positional argument '
                            f'that is a dict. Got {args}')

        for resource_name, transformer in self.transformers.items():
            if resource_name in other:
                new_resource = transformer(other[resource_name],
                                           resource_name)
                other.update({resource_name: new_resource})
            if resource_name in kwargs:
                new_resource = transformer(kwargs[resource_name],
                                           resource_name)
                kwargs.update({resource_name: new_resource})

        return super().update(other, **kwargs)


resources = ResourceManager()

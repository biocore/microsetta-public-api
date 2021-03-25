import os
import pandas as pd
import biom
from copy import deepcopy
from microsetta_public_api.exceptions import ConfigurationError
from skbio.stats.ordination import OrdinationResults
from qiime2.core.type.grammar import TypeExp
from qiime2 import Artifact, Metadata
from qiime2.metadata.io import MetadataFileError
from q2_types.sample_data import AlphaDiversity, SampleData
from q2_types.feature_table import FeatureTable, Frequency
from q2_types.feature_data import FeatureData, Taxonomy
from q2_types.ordination import PCoAResults

from microsetta_public_api._logging import timeit
from microsetta_public_api.models._taxonomy import Taxonomy as TaxonomyModel


@timeit('_dict_of_literals_to_dict')
def _dict_of_literals_to_dict(dict_of_detail, resource_name):
    # passthrough
    return dict_of_detail


@timeit('_dict_of_paths_to_alpha_data')
def _dict_of_paths_to_alpha_data(dict_of_qza_paths, resource_name):
    _validate_dict_of_paths(dict_of_qza_paths,
                            resource_name)
    new_resource = _replace_paths_with_qza(dict_of_qza_paths,
                                           SampleData[AlphaDiversity],
                                           view_type=pd.Series)
    return new_resource


@timeit('_dict_of_paths_to_pcoa')
def _dict_of_paths_to_pcoa(dict_of_qza_paths, resource_name):
    _validate_dict_of_paths(dict_of_qza_paths,
                            resource_name)
    new_resource = _replace_paths_with_qza(dict_of_qza_paths,
                                           PCoAResults,
                                           view_type=OrdinationResults)
    return new_resource


@timeit('_dict_of_dict_of_paths_to_pcoa')
def _dict_of_dict_of_paths_to_pcoa(dict_of_dict_of_qza_paths, resource_name):
    new_resource = dict()
    for key, value in dict_of_dict_of_qza_paths.items():
        new_resource[key] = _dict_of_paths_to_pcoa(value, resource_name)
    return new_resource


@timeit('_transform_dict_of_table')
def _transform_dict_of_table(dict_, resource_name):
    if not isinstance(dict_, dict):
        raise TypeError(f"Expected field '{resource_name}' to contain a "
                        f"dictionary. Got {dict_}.")
    new_resource = dict()
    for table_name, attributes in dict_.items():
        res = _transform_single_table(attributes, table_name)
        new_resource[table_name] = res
    return new_resource


@timeit('_transform_single_table')
def _transform_single_table(dict_, resource_name):
    taxonomy = {'feature-data-taxonomy': dict_.pop('feature-data-taxonomy',
                                                   None)}
    supported_table_types = {'qza', 'biom'}
    table_type = dict_.get('table-format', 'qza')
    if table_type not in supported_table_types:
        raise ValueError(f"'table-format'={table_type} not in supported table "
                         f"types: {supported_table_types}.")

    _validate_dict_of_paths(dict_, resource_name, allow_none=True,
                            required_fields=['table'],
                            non_ext_entries=['q2-type', 'table-format',
                                             'cache-taxonomy'],
                            allow_extras=True,
                            extensions=['.' + table_type]
                            )
    _validate_dict_of_paths(taxonomy, resource_name,
                            allow_none=True,
                            )

    if taxonomy['feature-data-taxonomy'] is not None:
        dict_.update(taxonomy)

    semantic_types = {
        'feature-data-taxonomy': FeatureData[Taxonomy],
    }
    biom_kws = set()
    if table_type == 'qza':
        semantic_types.update({
            'table': dict_.get('table-type', FeatureTable[Frequency]),
            'variances': FeatureTable[Frequency],
        })
    elif table_type == 'biom':
        biom_kws.update({'table', 'variances'})
    else:
        # shouldn't happen because error check earlier but seems better than
        # silently ignoring....
        raise ValueError(f"'table-type'={table_type} not in supported table "
                         f"types: {supported_table_types}.")

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
        elif key in biom_kws:
            new_resource[key] = biom.load_table(value)

    cache_taxonomy = new_resource.get('cache-taxonomy', True)
    if 'feature-data-taxonomy' in new_resource and cache_taxonomy:
        table = new_resource['table']
        taxonomy = new_resource['feature-data-taxonomy']
        variances = new_resource.get('variances', None)

        # rank_level=5 -> genus
        model = TaxonomyModel(table, taxonomy, variances, rank_level=5)
        new_resource['model'] = model

    return new_resource


@timeit('_parse_q2_data')
def _parse_q2_data(filepath, semantic_type, view_type=None,
                   ignore_predicate=True):
    try:
        data = _q2_load(filepath)
    except ValueError as e:
        raise ConfigurationError(*e.args)

    data_type = data.type
    if ignore_predicate:
        data_type = TypeExp(data_type.template, fields=data_type.fields)

    if data_type != semantic_type:
        raise ConfigurationError(f"Expected QZA '{filepath}' to have type "
                                 f"'{semantic_type}'. "
                                 f"Received '{data.type}'.")
    if view_type is not None:
        data = _q2_view(data, view_type)

    return data


@timeit('_q2_view')
def _q2_view(data, view_type):
    data = data.view(view_type=view_type)
    return data


@timeit('_q2_load')
def _q2_load(filepath):
    data = Artifact.load(filepath)
    return data


@timeit('_validate_dict_of_paths')
def _validate_dict_of_paths(dict_of_paths, name, allow_none=False,
                            required_fields=None, allow_extras=False,
                            non_ext_entries=None, extensions=None,
                            ):
    if extensions is None:
        extensions = ['.qza']
    if non_ext_entries is None:
        non_ext_entries = []
    if not isinstance(dict_of_paths, dict):
        raise ValueError(f"Expected '{name}' field to contain a dict. "
                         f"Got {type(dict_of_paths).__name__}")
    if required_fields:
        for field in required_fields:
            if field not in dict_of_paths:
                raise ValueError(f"Did not get required field '{field}'.")
        if not allow_extras:
            allowed_keys = set(required_fields) | set(non_ext_entries)
            extra_keys = list(filter(lambda x: x not in allowed_keys,
                                     dict_of_paths.keys()))
            if extra_keys:
                raise ValueError(f"Extra keys: {extra_keys} not allowed.")

    for key, value in dict_of_paths.items():
        if key in non_ext_entries:
            continue
        has_ext = isinstance(value, str) and value.endswith(tuple(extensions))
        exists = isinstance(value, str) and os.path.exists(value)
        is_none = value is None
        value_is_existing_qza_path = (has_ext and exists) or \
                                     (is_none and allow_none)

        if not value_is_existing_qza_path:
            exp_ext = extensions[0] if len(extensions) == 1 else extensions
            raise ValueError('Expected existing path with {} '
                             'extension. Got: {}'.format(exp_ext, value))


@timeit('_replace_paths_with_qza')
def _replace_paths_with_qza(dict_of_qza_paths, semantic_type, view_type=None):
    new_resource = dict()
    for key, value in dict_of_qza_paths.items():
        new_resource[key] = _parse_q2_data(value,
                                           semantic_type,
                                           view_type=view_type,
                                           )
    return new_resource


@timeit('_load_q2_metadata')
def _load_q2_metadata(metadata_path, name):
    try:
        new_resource = Metadata.load(metadata_path)
    except TypeError:
        # if metadata_path is some type that does not have '+' method with
        #  str, e.g., dict then q2 metadata will get a type error. Except this
        #  error and give a MetadataFileError, which is more informative
        raise MetadataFileError(str(metadata_path))
    return new_resource.to_dataframe()


@timeit('_load_neighbors_tsv')
def _load_neighbors_tsv(dict_of_paths, name):
    new_resource = dict()
    for key, value in dict_of_paths.items():
        new_resource[key] = pd.read_csv(value, sep='\t',
                                        dtype=str).set_index('sample_id')
    return new_resource


class ResourceManager(dict):

    transformers = {
        'alpha_resources': _dict_of_paths_to_alpha_data,
        'table_resources': _transform_dict_of_table,
        'pcoa': _dict_of_dict_of_paths_to_pcoa,
        'metadata': _load_q2_metadata,
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
        ...             'table': '/path/to/feature-table.biom',
        ...             'feature-data-taxonomy': '/a/feat-data-taxonomy.qza',
        ...             'variances': '/a/variance/feature-table.qza',
        ...             'table-format': 'biom'
        ...         },
        ...         'some_other_feature_table': {
        ...             'table': '/another/path/tofeature-table.qza',
        ...             'variances': '/a/variance/feature-table.qza',
        ...             'q2-type': FeatureTable[Frequency],
        ...         },
        ...     },
        ...     pcoa={
        ...         'fecal': {
        ...             'unifrac': '/a/pcoa/path1.qza',
        ...             'jaccard': '/another/pcoa/path2.qza',
        ...         },
        ...         'all_samples': {
        ...             'unifrac': '/a/path/to/all_samples/pcoa.qza',
        ...         }
        ...     },
        ...     metadata='/path/to/some/metadata.txt',
        ...     some_other_resource='here is a string resource',
        ...     )

        """
        to_add = dict()
        if len(args) == 1 and isinstance(args[0], dict):
            other = args[0]
        elif len(args) == 0:
            other = dict()
        else:
            raise TypeError(f'update expected at most 1 positional argument '
                            f'that is a dict. Got {args}')

        to_add.update(other, **kwargs)

        for resource_name, transformer in self.transformers.items():
            if resource_name in other:
                new_resource = transformer(other[resource_name],
                                           resource_name)
                to_add.update({resource_name: new_resource})
            if resource_name in kwargs:
                new_resource = transformer(kwargs[resource_name],
                                           resource_name)
                to_add.update({resource_name: new_resource})

        return dict.update(self, to_add, **kwargs)


resources = ResourceManager()

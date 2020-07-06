from collections import namedtuple, OrderedDict
from typing import Iterable, Dict, Optional, List
from abc import abstractmethod

import skbio
import biom
import numpy as np
import pandas as pd

from microsetta_public_api.exceptions import DisjointError, UnknownID
from microsetta_public_api.utils import DataTable
from ._base import ModelBase

_gt_named = namedtuple('GroupTaxonomy', ['name', 'taxonomy', 'features',
                                         'feature_values', 'feature_variances',
                                         'feature_ranks'])


class GroupTaxonomy(_gt_named):
    """Minimal information to characterize taxonomic detail of a group

    A group may represent the taxonomic detail of a single sample. Or, a group
    may represent the summarized taxonomic detail of many samples (such as
    all fecal samples).

    Attributes
    ----------
    name : str
        The name of the group (e.g., 'sample-foo')
    taxonomy : str
        A newick string of the taxonomy represented
    features : list of str
        The names of the features represented by the group
    feature_values : list of float
        Values associated with the features (e.g., relative abundance, rank,
        etc)
    feature_variances : list of float
        Values associated with the variance of the features
    feature_ranks : list of float
        Values associated with the rank of the features. For example, if
        an instance represents multiple samples (e.g., all fecal samples), then
        feature_ranks would describe the median rank for a corresponding
        feature.

    Notes
    -----
    A feature need not be a tip of the taxonomy. However, caution is advised
    over possible nesting interpretation if representing sum-to-one data at
    multiple levels.
    """
    __slots__ = ()

    def __init__(self, *args, name=None, taxonomy=None, features=None,
                 feature_values=None, feature_variances=None,
                 feature_ranks=None,
                 ):
        if args:
            raise NotImplementedError("%s only supports kwargs" %
                                      str(self.__class__))

        for k in features:
            # a _very_ lightweight check to avoid expense of full newick parse.
            # this is not a perfect sanity test
            if k not in taxonomy:
                raise UnknownID("%s is not in the taxonomy." % k)

        if (features and (feature_values is None)) or len(features) != len(
                feature_values):
            raise ValueError("features and feature_values have a length "
                             "mismatch")

        if feature_variances is not None and len(features) != len(
                feature_variances):
            raise ValueError("features and feature_variances have a length "
                             "mismatch")

        if feature_ranks is not None and len(features) != len(feature_ranks):
            raise ValueError("features and feature_ranks have a length "
                             "mismatch")

        super().__init__()

    def to_dict(self) -> Dict:
        return self._asdict()

    def __str__(self) -> Dict:
        return str(self.to_dict())


class Taxonomy(ModelBase):
    """Represent the full taxonomy and facilitate table oriented retrieval"""

    def __init__(self, table: biom.Table, features: pd.DataFrame,
                 variances: biom.Table = None):
        """Establish the taxonomy data

        Parameters
        ----------
        table : biom.Table
            Relative abundance data per sample or collapsed into higher order
            entiries (e.g., abx in the past year)
        features : pd.DataFrame
            DataFrame relating an observation to a Taxon
        variances : biom.Table, optional
            Variation information about a taxon within a label.
        """
        self._table = table.norm(inplace=False)
        self._group_id_lookup = set(self._table.ids())
        self._feature_id_lookup = set(self._table.ids(axis='observation'))
        self._feature_order = self._table.ids(axis='observation')
        self._features = features
        self._ranks = table.rankdata(inplace=False)

        if variances is None:
            self._variances = biom.Table(np.zeros(self._table.shape),
                                         self._table.ids(axis='observation'),
                                         self._table.ids())
        else:
            self._variances = variances

        if set(self._variances.ids()) != set(self._table.ids()):
            raise DisjointError("Table and variances are disjoint")

        if set(self._variances.ids(axis='observation')) != \
                set(self._table.ids(axis='observation')):
            raise DisjointError("Table and variances are disjoint")

        if set(self._table.ids(axis='observation')) != \
                set(self._features.index):
            raise DisjointError("Table and features are disjoint")

        self._features = self._features.loc[self._feature_order]
        self._variances = self._variances.sort_order(self._feature_order,
                                                     axis='observation')

    def _get_sample_ids(self) -> np.ndarray:
        return self._table.ids()

    def _get_feature_ids(self) -> np.ndarray:
        return self._table.ids(axis='observation')

    def get_group_raw(self, ids: Iterable[str] = None, name: str = None):
        """Get raw values for a set of IDs"""
        # NOTE: not sure if needed for Taxonomy
        raise NotImplementedError

    def get_group(self, ids: Iterable[str], name: str = None) -> GroupTaxonomy:
        """Get taxonomic detail for a given group

        Parameters
        ----------
        ids : list of str
            The identifiers of a group to obtain
        name : str
            The name of the set of group. It must be provided if multiple
            IDs are requested.

        Raises
        ------
        UnknownID
            If an identifier is not present in the data.
        ValueError
            If a name is not specified when asking for multiple IDs

        Returns
        -------
        GroupTaxonomy
            Taxonomic detail associated with the ID
        """
        for i in ids:
            if i not in self._group_id_lookup:
                raise UnknownID('%s does not exist' % i)

        if len(ids) > 1:
            if name is None:
                raise ValueError("Name not specified.")

            table = self._table.filter(set(ids), inplace=False).remove_empty()
            features = table.ids(axis='observation')
            feature_values = table.sum('observation')
            feature_values /= feature_values.sum()
            feature_variances = [0.] * len(feature_values)
        else:
            id_ = ids[0]
            name = id_

            # get data, pull feature ids out. Zeros are not an issue here as
            # if it were zero, that means the feature isn't present
            group_vec = self._table.data(id_, dense=False)
            features = self._feature_order[group_vec.indices]
            feature_values = group_vec.data

            # handle variances, which may have zeros
            feature_variances = self._variances.data(id_,
                                                     dense=True)
            feature_variances = feature_variances[group_vec.indices]

        # construct the group specific taxonomy
        feature_taxons = self._features.loc[features]
        tree_data = ((i, lineage.split('; '))
                     for i, lineage in feature_taxons['Taxon'].items())
        taxonomy = skbio.TreeNode.from_taxonomy(tree_data)

        return GroupTaxonomy(name=name,
                             taxonomy=str(taxonomy).strip(),
                             features=list(features),
                             feature_values=list(feature_values),
                             feature_variances=list(feature_variances),
                             feature_ranks=None,
                             )

    def presence_data_table(self, ids: Iterable[str],
                            formatter: Optional['Formatter'] = None) -> \
            DataTable:
        if formatter is None:
            formatter: Formatter = GreengenesFormatter()
        table = self._table.filter(set(ids), inplace=False).remove_empty()
        features = table.ids(axis='observation')
        feature_taxons = self._features.loc[features]
        feature_data = {i: formatter.dict_format(lineage)
                        for i, lineage in feature_taxons['Taxon'].items()}

        entries = list()
        for vec, sample_id, _ in table.iter(dense=False):
            for feature_idx, val in zip(vec.indices, vec.data):
                entries.append({
                    **{'sampleId': sample_id,
                       'relativeAbundance': val},
                    **feature_data[features[feature_idx]],
                })

        sample_data = pd.DataFrame(entries,
                                   # this enforces the column order
                                   columns=['sampleId'] + formatter.labels +
                                           ['relativeAbundance'],
                                   # need the .astype('object') in case a
                                   # column is completely empty (filled with
                                   # Nan, default dtype is numeric,
                                   # which cannot be replaced with None.
                                   # Need None because it is valid for JSON,
                                   # but NaN is not.
                                   ).astype('object')
        sample_data[pd.isna(sample_data)] = None
        return DataTable.from_dataframe(sample_data)


class Formatter:

    labels: List

    @abstractmethod
    def dict_format(self, taxonomy_string):
        raise NotImplementedError()


class GreengenesFormatter(Formatter):
    _map = OrderedDict(k__='Kingdom', p__='Phylum', c__='Class',
                       o__='Order', f__='Family', g__='Genus', s__='Species')
    labels = list(_map.values())

    @classmethod
    def dict_format(cls, taxonomy_string: str):
        ranks = taxonomy_string.split('; ')
        formatted = OrderedDict()

        for rank in ranks:
            name = rank[:3]
            if name in cls._map:
                formatted[cls._map[name]] = rank[3:]

        return formatted

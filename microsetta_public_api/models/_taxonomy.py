from collections import namedtuple, OrderedDict, Counter
from typing import Iterable, Dict, Optional, List
from abc import abstractmethod

import skbio
from skbio import TreeNode
import biom
import numpy as np
import pandas as pd
import scipy.sparse as ss
from bp import parse_newick

from microsetta_public_api.exceptions import (DisjointError, UnknownID,
                                              SubsetError)
from microsetta_public_api.utils import DataTable
from ._base import ModelBase

_gt_named = namedtuple('GroupTaxonomy', ['name', 'taxonomy', 'features',
                                         'feature_values',
                                         'feature_variances'])


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

    Notes
    -----
    A feature need not be a tip of the taxonomy. However, caution is advised
    over possible nesting interpretation if representing sum-to-one data at
    multiple levels.
    """
    __slots__ = ()

    def __init__(self, *args, name=None, taxonomy=None, features=None,
                 feature_values=None, feature_variances=None):
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

        super().__init__()

    def to_dict(self) -> Dict:
        return self._asdict()

    def __str__(self) -> Dict:
        return str(self.to_dict())


def get_lineage_max_level(features, max_level):
    """

    Parameters
    ----------
    features : iterable of str
        Contains taxonomy strings to create lineage tuples for (see also
        skbio.TreeNode.from_taxonomy)
    max_level : int
        Maximum number of levels to include in the lineage tuples

    Returns
    -------

    """
    # set ensures there are not duplicate lineages
    lineages = set()
    for lineage in features:
        lineage = [taxon.lstrip() for taxon in lineage.split(';')]

        for i, level in enumerate(lineage):
            # ensure ambiguous taxa like 'g__' are not added
            split_lineage = level.split('__')
            if (len(split_lineage) > 1) and (len(split_lineage[1]) < 1):
                lineage = lineage[0:i]
                break

        # take out anything that is below max level
        lineage = lineage[:max_level]

        # lineages.add((lineage.pop(), tuple(lineage)))
        lineages.add(tuple(lineage))
    return lineages


def create_tree_node_from_lineages(lineages):
    """

    Parameters
    ----------
    lineages : iterable of str

    length : callable

    Returns
    -------
    TreeNode
        Built on the given lineages

    """
    root = TreeNode(length=1)
    for lineage in lineages:
        current_root = root
        for i, taxon in enumerate(lineage):
            child_matches = False
            # see if any children of root match name of this taxon
            parts = (current_root.name, taxon) if current_root.name else (
                taxon,)
            node_name = '; '.join(parts)
            for child in current_root.children:
                if child.name == node_name:
                    child_matches = True
                    current_root = child
                    break

            if not child_matches:
                new_node = TreeNode(name=node_name, length=1)
                current_root.append(new_node)
                current_root = new_node

    return root


class Taxonomy(ModelBase):
    """Represent the full taxonomy and facilitate table oriented retrieval"""

    def __init__(self, table: biom.Table, features: pd.DataFrame,
                 variances: biom.Table = None,
                 formatter: Optional['Formatter'] = None,
                 rank_level: int = 1,
                 collapse_level: int = 6,
                 ):
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
        rank_level : int
            The taxonomic level (depth) to compute ranks over. Level 0 is
            domain, level 1 is phylum, etc.
        collapse_level : int
            The taxonomic level to collapse for additional tree
            representations.
        """
        self._table = table.norm(inplace=False)
        self._group_id_lookup = set(self._table.ids())
        self._feature_id_lookup = set(self._table.ids(axis='observation'))
        self._feature_order = self._table.ids(axis='observation')
        self._features = features

        if variances is None:
            empty = ss.csr_matrix((len(self._table.ids(axis='observation')),
                                   len(self._table.ids())), dtype=float)
            self._variances = biom.Table(empty,
                                         self._table.ids(axis='observation'),
                                         self._table.ids())
        else:
            self._variances = variances

        if set(self._variances.ids()) != set(self._table.ids()):
            raise DisjointError("Table and variances are disjoint")

        if set(self._variances.ids(axis='observation')) != \
                set(self._table.ids(axis='observation')):
            raise DisjointError("Table and variances are disjoint")

        if not self._feature_id_lookup.issubset(set(self._features.index)):
            raise SubsetError("Table features are not a subset of the "
                              "taxonomy information")

        self._ranked, self._ranked_order = self._rankdata(rank_level)

        self._features = self._features.loc[self._feature_order]
        self._variances = self._variances.sort_order(self._feature_order,
                                                     axis='observation')

        if formatter is None:
            formatter: Formatter = GreengenesFormatter()
        self._formatter = formatter

        # initialize taxonomy tree
        tree_data = ((i, [taxon.lstrip() for taxon in lineage.split(';')])
                     for i, lineage in self._features['Taxon'].items())
        self.taxonomy_tree = skbio.TreeNode.from_taxonomy(tree_data)
        self._index_taxa_prevalence()

        feature_metadata = dict()
        for feature, taxonomy in self._features.to_dict()['Taxon'].items():
            taxonomy_list = [clade.strip() for clade in taxonomy.split(';')]

            feature_metadata[feature] = {
                'taxonomy': taxonomy_list,
            }

        self.bp_tree = self._construct_bp_tree(feature_metadata,
                                               collapse_level=collapse_level)

        feature_taxons = self._features
        self._formatted_taxa_names = {i: self._formatter.dict_format(lineage)
                                      for i, lineage in
                                      feature_taxons['Taxon'].items()}

    def _construct_bp_tree(self, feature_metadata, collapse_level):
        self._table.add_metadata(feature_metadata,
                                 axis='observation')

        def partition_f(id_, metadata):
            return '; '.join(metadata['taxonomy'][:collapse_level])

        self._collapsed_table = self._table.collapse(partition_f,
                                                     axis='observation')
        collapsed_taxonomy = []
        for lineage_str in self._collapsed_table.ids('observation'):
            clades = lineage_str.split('; ')
            lineage_list = []
            current_clade = clades[0]
            for internal_node in clades[1:]:
                # by convention, all non-leaf nodes should end wiht ';'
                # so that the same label can be applied to both one internal
                # node and one external node and still have 'unique' ids,
                # e.g.: ((('a; b; c')'a; b;',('a; f; g')'a; f;')'a;',a);
                # this should also allow us to identify the tips present in
                # a sample by directly taking the ids from the table
                current_clade += ';'
                lineage_list.append(current_clade)
                current_clade += (' ' + internal_node)
            collapsed_taxonomy.append((current_clade, lineage_list))
        self._collapsed_taxonomy = collapsed_taxonomy
        self._collapsed_taxonomy_tree = TreeNode.from_taxonomy(
            collapsed_taxonomy)
        for node in self._collapsed_taxonomy_tree.traverse():
            node.length = 1

        return parse_newick(str(self._collapsed_taxonomy_tree))

    def _rankdata(self, rank_level) -> (pd.DataFrame, pd.Series):
        # it seems QIIME regressed and no longer produces stable taxonomy
        # strings. Yay.
        index = {}
        for idx, v in self._features['Taxon'].items():
            parts = v.split(';')
            if len(parts) <= rank_level:
                continue
            else:
                index[idx] = parts[rank_level].split('__')[-1].strip()

        def collapse(i, m):
            return index.get(i, 'Non-specific')

        base = self._table.collapse(collapse, axis='observation', norm=False)

        # 16S mitochondria reads report as g__human
        keep = {v for v in base.ids(axis='observation')
                if 'human' not in v.lower()}
        keep -= {None, "", 'Non-specific', 'g__'}
        base.filter(keep, axis='observation')

        # reduce to the top observed taxa
        median_order = self._rankdata_order(base)
        base.filter(set(median_order.index), axis='observation')
        base.rankdata(inplace=True)

        # convert to a melted dataframe
        base_df = base.to_dataframe(dense=True)
        base_df.index.name = 'Taxon'
        base_df_melted = base_df.reset_index().melt(id_vars=['Taxon'],
                                                    value_name='Rank')
        base_df_melted = base_df_melted[base_df_melted['Rank'] > 0]
        base_df_melted.rename(columns={'variable': 'Sample ID'}, inplace=True)

        return base_df_melted, median_order

    def _rankdata_order(self, table, top_n=50) -> pd.Series:
        # rank by median
        medians = []
        for v in table.iter_data(axis='observation', dense=False):
            medians.append(np.median(v.data))

        medians = pd.Series(medians, index=table.ids(axis='observation'))
        ordered = medians.sort_values(ascending=False).head(top_n)
        ordered.loc[:] = np.arange(0, len(ordered), dtype=int)
        return ordered

    def _index_taxa_prevalence(self):
        """Cache the number of samples each taxon was observed in"""
        features = self._table.ids(axis='observation')
        n_samples = len(self._table.ids())
        table_pa = self._table.pa(inplace=False)

        # how many samples a feature was observed in
        sample_counts = pd.Series(table_pa.sum('observation'),
                                  index=features)
        self.feature_uniques = sample_counts == 1
        self.feature_prevalence = (sample_counts / n_samples)

    def rare_unique(self, id_, rare_threshold=0.1):
        """Obtain the rare and unique features for an ID

        Parameters
        ----------
        id_ : str
            The identifier to obtain rare/unique information for
        rare_threshold : float
            The threshold to consider a feature rare. Defaults to 0.1,
            which is the historical rare value from the AGP

        Raises
        ------
        UnknownID
            If the requested sample is not present

        Returns
        -------
        dict
            {'rare': {feature: prevalence}, 'unique': [feature, ]}
        """
        if id_ not in self._group_id_lookup:
            raise UnknownID('%s does not exist' % id_)

        sample_data = self._table.data(id_, dense=False)

        # self.feature_prevalence and self.feature_uniques are derived from
        # self._table so the ordering of features is consistent
        sample_prevalences = self.feature_prevalence.iloc[sample_data.indices]
        sample_uniques = self.feature_uniques.iloc[sample_data.indices]

        rare_at_threshold = sample_prevalences < rare_threshold
        if rare_at_threshold.sum() == 0:
            rares = None
        else:
            rares = sample_prevalences[rare_at_threshold].to_dict()

        if sample_uniques.sum() == 0:
            uniques = None
        else:
            uniques = list(sample_uniques[sample_uniques].index)

        return {'rare': rares, 'unique': uniques}

    def ranks_sample(self, sample_size: int) -> pd.DataFrame:
        """Randomly sample, without replacement, from ._ranked

        Parameters
        ----------
        sample_size : int
            The number of elements to obtain. If value is greater than the
            total number of entries in .ranked, all entries of .ranked will
            be returned. If the value is less than zero, no values will be
            returned

        Returns
        -------
        pd.DataFrame
            The subset of .ranked
        """
        if sample_size < 0:
            sample_size = 0

        n_rows = len(self._ranked)
        return self._ranked.sample(min(sample_size, n_rows), replace=False)

    def ranks_specific(self, sample_id: str) -> pd.DataFrame:
        """Obtain the taxonomy rank information for a specific sample

        Parameters
        ----------
        sample_id : str
            The sample identifier to obtain ranks for

        Raises
        ------
        UnknownID
            If the requested sample is not present

        Returns
        -------
        pd.DataFrame
            The subset of .ranked for the sample
        """
        subset = self._ranked[self._ranked['Sample ID'] == sample_id]
        if len(subset) == 0:
            raise UnknownID("%s not found" % sample_id)
        else:
            return subset.copy()

    def ranks_order(self, taxa: Iterable[str] = None) -> List:
        """Obtain the rank order of the requested taxa names

        Parameters
        ----------
        taxa : Iterable[str], optional
            The taxa to request ordering for. If not specified, return the
            order of all contained taxa

        Raises
        ------
        UnknownID
            If a requested taxa is not ranked or otherwise unknown

        Returns
        -------
        list
            The order of the taxa, where index 0 corresponds to the highest
            ranked taxon, index 1 the next highest, etc
        """
        if taxa is None:
            taxa = set(self._ranked_order.index)
        else:
            taxa = set(taxa)
            known = set(self._ranked_order.index)

            unk = taxa - known
            if len(unk) > 0:
                raise UnknownID("One or more names are not in the top "
                                "ranks: %s" % ",".join(unk))

        return [t for t in self._ranked_order.index if t in taxa]

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
        tree_data = ((i, [taxon.lstrip() for taxon in lineage.split(';')])
                     for i, lineage in feature_taxons['Taxon'].items())
        taxonomy = skbio.TreeNode.from_taxonomy(tree_data)
        taxonomy = self._taxonomy_tree_from_features(features)

        return GroupTaxonomy(name=name,
                             taxonomy=str(taxonomy).strip(),
                             features=list(features),
                             feature_values=list(feature_values),
                             feature_variances=list(feature_variances),
                             )

    def _taxonomy_tree_from_features(self, features):
        """Construct a skbio.TreeNode based on the provided features"""
        feature_taxons = self._features.loc[features]
        tree_data = ((i, [taxon.lstrip() for taxon in lineage.split(';')])
                     for i, lineage in feature_taxons['Taxon'].items())
        return skbio.TreeNode.from_taxonomy(tree_data)

    def get_counts(self, level, samples=None) -> dict:
        """Obtain the number of unique maximal specificity features

        Parameters
        ----------
        level : str
            The level to obtain feature counts for.
        samples : str or iterable of str, optional
            The samples to collect data for. If not provided, counts are
            derived from all samples.

        Returns
        -------
        dict
            The {taxon: count} observed. The count corresponds to the greatest
            taxonomic specificity in the data. As an example, if counting at
            the phylum level, and FOO had 2 classified genera and a classified
            family without named genera, the count returned would be {FOO: 3}.
            The count is the number of features corresponding to the given
            taxon that are present in any of the given samples.
        """
        if samples is None:
            table = self._table
        elif isinstance(samples, str):
            table = self._table.filter({samples, },
                                       inplace=False).remove_empty()
        else:
            table = self._table.filter(set(samples),
                                       inplace=False).remove_empty()

        feature_taxons = self._features.loc[table.ids(axis='observation')]
        ftn = self._formatted_taxa_names
        observed = Counter([ftn[i].get(level, 'Unidentified')
                            for i in feature_taxons.index])
        return observed

    def presence_data_table(self, ids: Iterable[str]) -> DataTable:
        table = self._table.filter(set(ids), inplace=False).remove_empty()
        features = table.ids(axis='observation')

        entries = list()
        for vec, sample_id, _ in table.iter(dense=False):
            for feature_idx, val in zip(vec.indices, vec.data):
                entry = {
                    'sampleId': sample_id,
                    'relativeAbundance': val,
                    **self._formatted_taxa_names[features[feature_idx]],
                }
                entries.append(entry)

        sample_data = pd.DataFrame(
            entries,
            # this enforces the column order
            columns=['sampleId'] + self._formatter.labels + [
                'relativeAbundance'],
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

    @classmethod
    @abstractmethod
    def dict_format(cls, taxonomy_string):
        raise NotImplementedError()


class GreengenesFormatter(Formatter):
    _map = OrderedDict(k__='Kingdom', p__='Phylum', c__='Class',
                       o__='Order', f__='Family', g__='Genus', s__='Species')
    labels = list(_map.values())

    @classmethod
    def dict_format(cls, taxonomy_string: str):
        ranks = [rank_.strip() for rank_ in taxonomy_string.split(';')]
        formatted = OrderedDict()

        for rank in ranks:
            name = rank[:3]
            if name in cls._map:
                formatted[cls._map[name]] = rank[3:]

        return formatted

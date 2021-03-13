from typing import Dict
import numpy as np
import pandas as pd
from q2_types.distance_matrix import DistanceMatrix as DistanceMatrixType
from skbio.stats.distance import DistanceMatrix
from microsetta_public_api.resources import (
    _validate_dict_of_paths,
    _replace_paths_with_qza,
)


def _closest_k_from_distance_matrix(dm, k):
    """Constructs a dataframe containing only the closest k samples per sample

    Parameters
    ----------
    dm : skbio.DistanceMatrix
        The distance matrix to operate on
    k : int
        The number of samples to retain

    Returns
    -------
    pd.DataFrame
        Indexed by sample ID, the columns correspond to k0, k1, ... and
        the frame is valued by those similar sample IDs
    """
    results = []
    for sample_id in dm.ids:
        sample_idx = dm.index(sample_id)
        distances = dm[sample_idx]
        # has indices partitioned by distance, around the `kth` entry of the
        # array
        idx = np.argpartition(distances, kth=k)
        # get the k + 1 closest samples (including this sample)
        k_nearest_idx = idx[:k + 1]
        # sort the k closest samples by their distance, so the closest are
        k_distances = distances[k_nearest_idx]
        # remove the sample itself
        sorted_k_indices = np.argsort(k_distances)[1:]
        k_nearest_idx = k_nearest_idx[sorted_k_indices]
        nearest = [sample_id] + [dm.ids[idx]
                                 for idx in k_nearest_idx]
        results.append(nearest)

    df = pd.DataFrame(results,
                      columns=['sample_id'] + ['k%d' % i for i in range(k)])
    return df.set_index('sample_id')


def _dict_of_paths_to_beta_data(dict_of_qza_paths, resource_name) -> \
        Dict[str, DistanceMatrix]:
    _validate_dict_of_paths(dict_of_qza_paths,
                            resource_name)
    new_resource = _replace_paths_with_qza(dict_of_qza_paths,
                                           DistanceMatrixType,
                                           view_type=DistanceMatrix,
                                           )
    key = list(new_resource.keys())[0]
    dm = new_resource[key]
    max_n_neighbors = 100
    k = min(len(dm.ids) - 1, max_n_neighbors)
    new_resource[key] = _closest_k_from_distance_matrix(dm, k)
    return new_resource

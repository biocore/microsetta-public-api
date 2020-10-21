from microsetta_public_api.repo._base import DiversityRepo
from microsetta_public_api.exceptions import UnknownID, InvalidParameter
import numpy as np


class BetaRepo(DiversityRepo):

    def __init__(self, resources):
        super().__init__(resources)
        self._ids = {key: set(dm.ids) for key, dm in resources.items()}

    def exists(self, sample_ids, metric):
        distance_matrix = self._get_resource(metric)
        if isinstance(sample_ids, str):
            return sample_ids in distance_matrix
        else:
            existing_ids = self._ids[metric]
            return [(id_ in existing_ids) for id_ in sample_ids]

    def k_nearest(self, sample_id, metric, k=1):
        distance_matrix = self._get_resource(metric)
        if not self.exists(sample_id, metric):
            raise UnknownID(sample_id)
        n_neighbors = len(distance_matrix.ids) - 1
        if k > n_neighbors:
            raise InvalidParameter(
                f"k={k} is greater than the number of neighbors of the "
                f"sample ID. Number of neighbors: {n_neighbors}"
            )
        # get
        sample_idx = distance_matrix.index(sample_id)
        distances = distance_matrix[sample_idx]
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
        return [distance_matrix.ids[idx] for idx in k_nearest_idx]

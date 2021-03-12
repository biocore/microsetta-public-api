from microsetta_public_api.repo._base import DiversityRepo
from microsetta_public_api.exceptions import UnknownID, InvalidParameter
import numpy as np


class BetaRepo(DiversityRepo):

    def __init__(self, resources):
        super().__init__(resources)

    def exists(self, sample_ids, metric):
        distance_matrix = self._get_resource(metric)
        if isinstance(sample_ids, str):
            return sample_ids in distance_matrix.index
        else:
            return [(id_ in distance_matrix.index) for id_ in sample_ids]

    def k_nearest(self, sample_id, metric, k=1):
        distance_matrix = self._get_resource(metric)
        if not self.exists(sample_id, metric):
            raise UnknownID(sample_id)
        n_neighbors = len(distance_matrix.columns)
        if k > n_neighbors:
            raise InvalidParameter(
                f"k={k} is greater than the maximum."
            )

        nearest = distance_matrix.loc[sample_id]
        return nearest[:k].to_list()

from microsetta_public_api.repo._base import DiversityRepo
from microsetta_public_api.exceptions import UnknownID, InvalidParameter


class NeighborsRepo(DiversityRepo):

    def __init__(self, resources):
        super().__init__(resources)

    def exists(self, sample_ids, metric):
        nearest_ids = self._get_resource(metric)
        if isinstance(sample_ids, str):
            return sample_ids in nearest_ids.index
        else:
            return [(id_ in nearest_ids.index) for id_ in sample_ids]

    def k_nearest(self, sample_id, metric, k=1):
        nearest_ids = self._get_resource(metric)
        if not self.exists(sample_id, metric):
            raise UnknownID(sample_id)
        n_neighbors = len(nearest_ids.columns)
        if k > n_neighbors:
            raise InvalidParameter(
                f"k={k} is greater than the maximum ({n_neighbors})."
            )

        nearest = nearest_ids.loc[sample_id]
        return nearest[:k].to_list()

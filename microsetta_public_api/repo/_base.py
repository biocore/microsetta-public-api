from abc import ABCMeta, abstractmethod
from microsetta_public_api.exceptions import UnknownMetric


class DiversityRepo(metaclass=ABCMeta):

    def __init__(self, resources):
        self._resources = resources

    # resources needs to be a property in order to be able to be
    #  mocked in the test cases, but also be instance specific
    @property
    def resources(self):
        return self._resources

    def _get_resource(self, metric):
        if metric not in self.available_metrics():
            raise UnknownMetric(f"No resource available for metric="
                                f"'{metric}'")
        else:
            res = self.resources.get(metric, None)
            return res

    def available_metrics(self):
        """Return the metrics that are available with this Repo

        Returns
        -------
        list of str:
            Names of metrics that this repo has configured.

        """
        return list(self.resources.keys())

    @abstractmethod
    def exists(self, sample_ids, metric):
        """Checks if sample_ids exist for the given metric.

        Parameters
        ----------
        sample_ids : str or list of str
            Ids for to check database for.

        metric : str
            Diversity metric.

        Returns
        -------
        bool or list of bool
            If sample_ids is str, then this returns a bool corresponding to
            whether the given sample ID exists. If given a list, each entry
            `i` corresponds to whether `sample_ids[i]` exists
            in the database.

        """
        pass

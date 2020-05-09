from microsetta_public_api.exceptions import UnknownMetric
from microsetta_public_api.resources import resources


class AlphaRepo:

    # resources needs to be a class variable in order to be able to be
    #  mocked in the test cases
    resources = dict()
    resource_locations = None

    def __init__(self):
        self.resources = resources.get('alpha_resources', dict())
        # if self.resource_locations is not None:
        #     # leaving as None here allows lazy loading of resources
        #     def f(x): return self._parse_q2_data(self.resource_locations[x])
        #     self.resources = {key: f(key) for key in self.resource_locations}

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

    def get_alpha_diversity(self, sample_ids, metric):
        """Obtains alpha diversity of a given metric for a list of samples.

        Parameters
        ----------
        sample_ids : str or list of str
            Ids for which to obtain alpha diversity measure.

        metric : str
            Alpha diversity metric.

        Returns
        -------
        pandas.Series
            Contains alpha diversity with metric `metric` for the
            union of samples ids in the database the ids in `sample_ids`.
            Sets the name of the series to `metric`.

        """
        # this could raise an UnknownMetric or ConfigurationError
        alpha_series = self._get_resource(metric)
        # TODO the following could throw KeyErrors if a sample id is not in
        #  the index. Right now, the API checks for missing ID's before
        #  calling this.
        if isinstance(sample_ids, str):
            return alpha_series.loc[[sample_ids]]
        else:
            return alpha_series.loc[sample_ids]

    def exists(self, sample_ids, metric):
        """Checks if sample_ids exist for the given metric.

        Parameters
        ----------
        sample_ids : str or list of str
            Ids for to check database for.

        metric : str
            Alpha diversity metric.

        Returns
        -------
        bool or list of bool
            If sample_ids is str, then this returns a bool corresponding to
            whether the given sample ID exists. If given a list, each entry
            `i` corresponds to whether `sample_ids[i]` exists
            in the database.

        """
        alpha_series = self._get_resource(metric)
        if isinstance(sample_ids, str):
            return sample_ids in alpha_series.index
        else:
            existing_ids = set(alpha_series.index)
            return [(id_ in existing_ids) for id_ in sample_ids]

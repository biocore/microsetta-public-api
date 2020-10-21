import pandas as pd
from microsetta_public_api.exceptions import UnknownID
from microsetta_public_api.repo._base import DiversityRepo
from microsetta_public_api.resources import resources as RESOURCES


class AlphaRepo(DiversityRepo):
    def __init__(self, resources=None):
        if resources is None:
            resources = RESOURCES.get('alpha_resources', dict())
        super().__init__(resources)

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

        Raises
        ------

        UnknownMetric
            If the metric is not in the repo's resources
        Unknown Id
            If the id does not have value for the requested metric

        """
        # this could raise an UnknownMetric or ConfigurationError
        alpha_series = self._get_resource(metric)
        if isinstance(sample_ids, str):
            ids = pd.Series([sample_ids])
        else:
            ids = pd.Series(sample_ids)
        unknown = ~ids.isin(alpha_series.index)
        if any(unknown):
            raise UnknownID(f"For metric='{metric}', unknown ids: "
                            f"{ids.loc[unknown]}")
        return alpha_series.loc[ids]

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

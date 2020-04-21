from collections import namedtuple
import pandas as pd
import numpy as np
from microsetta_public_api.models._base import ModelBase
from microsetta_public_api.models._exceptions import UnknownID
from typing import Dict, List

_gar_named = namedtuple('GroupAlphaRaw', ['name', 'alpha_metric', 'data'])

_ga_named = namedtuple('GroupAlpha', ['name', 'alpha_metric', 'mean', 'median',
                                      'std', 'group_size', 'percentile',
                                      'percentile_values'])


class GroupAlphaRaw(_gar_named):
    """Minimal information to characterize raw alpha values of a group

    A group may represent alpha detail of a single sample. Or, a group
    may represent the alpha values of many samples (such as all fecal samples).

    Attributes
    ----------
    name : str
        The name of the group.
    alpha_metric : str
        The name of the metric expressed.
    data : dict
        The sample to value data.
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        if args:
            raise NotImplementedError("%s only supports kwargs" %
                                      str(self.__class__))
        super()

    def to_dict(self) -> Dict:
        return self._asdict()

    def __str__(self) -> str:
        return str(self.to_dict())


class GroupAlpha(_ga_named):
    """Minimal information to characterize alpha detail of a group

    A group may represent alpha detail of a single sample. Or, a group
    may represent the summarized alpha distribution of many samples (such
    as all fecal samples).

    Attributes
    ----------
    name : str
        The name of the group (e.g., 'sample-foo').
    alpha_metric : str
        The name of the metric expressed.
    mean : float
        The mean of the group values.
    median : float
        The median of the group values.
    std : float
        The std of the group values.
    group_size : int
        The number of samples represented.
    percentile : list of int, optional
        The percentiles represented (e.g., 25th, 50th, 75th, etc) or None if
        the group_size is 1.
    percentile_values : list of float, optional
        The values of the percentiles or None if the group_size is 1.
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        if args:
            raise NotImplementedError("%s only supports kwargs" %
                                      str(self.__class__))

        if kwargs['group_size'] == 1:
            if not np.allclose(kwargs['mean'], kwargs['median']):
                raise ValueError('Data non-sensical for n=1.')

            if not np.allclose(kwargs['std'], 0.0):
                raise ValueError('Data non-sensical for n=1.')

            if kwargs['percentile'] is not None:
                raise ValueError('Data non-sensical for n=1.')

            if kwargs['percentile_values'] is not None:
                raise ValueError('Data non-sensical for n=1.')

        elif kwargs['group_size'] > 1:
            if kwargs['percentile'] is None:
                raise ValueError('Missing percentiles.')

            if kwargs['percentile_values'] is None:
                raise ValueError('Missing percentiles.')

            if len(kwargs['percentile']) != len(kwargs['percentile_values']):
                raise ValueError('Passing in unmatched percentiles.')

        else:
            raise ValueError('Instantiation with a bad group_size.')

        super()

    def to_dict(self) -> Dict:
        return self._asdict()

    def __str__(self) -> str:
        return str(self.to_dict())


class Alpha(ModelBase):
    def __init__(self, s: pd.Series,
                 percentiles: List = None):
        if percentiles is None:
            percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
        self._series = s
        self._percentiles = percentiles

    def _get_sample_ids(self) -> np.ndarray:
        return np.array(self._series.index)

    def _get_feature_ids(self) -> np.ndarray:
        return np.array([])

    def get_group_raw(self, ids: List[str] = None,
                      name: str = None) -> GroupAlphaRaw:
        """Get raw values for a set of IDs

        Parameters
        ----------
        ids : list of str, optional
            The IDs to obtain data for. If not specified, values for all IDs
            are returned
        name : str, optional
            The name of the group. A name must be specified if ids is not None.

        Raises
        ------
        UnknownID
            If a requested ID is not present
        ValueError
            If ids are specified but a name is not

        Returns
        -------
        GroupAlphaRaw
            The corresponding values for the requested IDs.
        """
        if ids is None:
            ids = self._get_sample_ids()
        else:
            if name is None:
                raise ValueError("Name not specified.")

        try:
            vals = self._series.loc[ids]
        except KeyError:
            raise UnknownID('Identifier not found.')

        return GroupAlphaRaw(name=name,
                             alpha_metric=self._series.name,
                             data=vals.to_dict())

    def get_group(self, ids: List[str], name: str = None) -> GroupAlpha:
        """Get group values

        Parameters
        ----------
        ids : list of str
            The IDs to represent the distribution
        name : str
            The name of the group. It must be provided if requesting multiple
            IDs

        Raises
        ------
        UnknownID
            If a requested ID is not present
        ValueError
            If a name is not specified when asking for multiple IDs.

        Returns
        -------
        GroupAlpha
            The corresponding distribution or individual data
        """
        try:
            vals = self._series.loc[ids]
        except KeyError:
            raise UnknownID('Identifier not found.')

        mean = vals.mean()
        median = vals.median()

        if len(ids) == 1:
            std = 0.
            return GroupAlpha(name=ids[0],
                              alpha_metric=self._series.name,
                              mean=mean,
                              median=median,
                              std=std,
                              group_size=1,
                              percentile=None,
                              percentile_values=None)
        else:
            if name is None:
                raise ValueError("Name not specified.")

            std = vals.std(ddof=0)
            percentile_values = np.percentile(vals, self._percentiles)
            return GroupAlpha(name=name,
                              alpha_metric=self._series.name,
                              mean=mean,
                              median=median,
                              std=std,
                              group_size=len(vals),
                              percentile=self._percentiles,
                              percentile_values=percentile_values)

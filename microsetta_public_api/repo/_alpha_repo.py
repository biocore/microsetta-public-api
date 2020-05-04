class AlphaRepo:

    def get_alpha_diversity(self, sample_ids, metric):
        """Obtains alpha diversity of a given metric for a list of samples.

        Parameters
        ----------
        sample_ids : list of str
            Ids for which to obtain alpha diversity measure.

        metric : str
            Alpha diversity metric.

        Returns
        -------
        pd.Series
            Contains alpha diversity with metric `metric` for the
            union of samples ids in the database the ids in `sample_ids`.
            Sets the name of the series to `metric`.

        """

        raise NotImplementedError

    def exists(self, sample_ids):
        """Checks if sample_ids exists in the database.

        Parameters
        ----------
        sample_ids : str or list of str
            Ids for to check database for.

        Returns
        -------
        bool or list of bool
            If sample_ids is str, then this returns a bool corresponding to
            whether the given sample ID exists. If given a list, each entry
            `i` corresponds to whether `sample_ids[i]` exists
            in the database.

        """

        raise NotImplementedError

class AlphaRepo:

    def get_alpha_diversity(self, sample_ids, metric):
        """

        Parameters
        ----------
        sample_ids : list of str
            Ids for which to obtain alpha diversity measure.

        metric : str
            Alpha diversity metric.

        Returns
        -------
        pd.Series
            Contains alpha diversity with metric `metric` for the samples in
            sample_ids with name=`metric`.

        Raises
        ------
        microsetta_public_api.models._exceptions.UknownID
            If an id in sample_ids does not exist in the database.

        """

        raise NotImplementedError

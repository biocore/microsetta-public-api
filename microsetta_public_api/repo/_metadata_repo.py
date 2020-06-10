class MetadataRepo:

    @property
    def metadata(self):
        raise NotImplementedError()

    @property
    def categories(self):
        raise NotImplementedError()

    def category_values(self, category):
        """
        Parameters
        ----------
        category : str
            Metadata category to return the values of

        Returns
        -------
        list
            Contains the unique values in the metadata category

        Raises
        ------
        ValueError
            If `category` is not an existing category in the metadata

        """
        raise NotImplementedError()

    def sample_id_matches(self, query):
        """
        Parameters
        ----------
        query : dict
            Expects a jquerybuilder formatted query

        Returns
        -------
        list
            The sample IDs that match the given `query`

        """
        raise NotImplementedError()

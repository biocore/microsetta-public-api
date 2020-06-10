from microsetta_public_api.resources import resources


class MetadataRepo:

    def __init__(self):
        self._metadata = resources.get('metadata', pd.DataFrame())

    @property
    def metadata(self):
        return self._metadata

    @property
    def categories(self):
        return list(self._metadata.columns)

    def category_values(self, category):
        if category not in self._metadata.columns:
            raise ValueError(f'No category with name `{category}`')
        else:
            return list(self._metadata[category].unique())

    def sample_id_matches(self, query):
        raise NotImplementedError()

from microsetta_public_api.resources import resources


class MetadataRepo:

    def __init__(self):
        raise NotImplementedError()

    @@property
    def categories(self):
        raise NotImplementedError()

    def category_values(self, category):
        raise NotImplementedError()

    def sample_id_matches(self, query):
        raise NotImplementedError()

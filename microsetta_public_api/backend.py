from abc import abstractmethod

from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.resources import _load_q2_metadata


class Loader:

    @abstractmethod
    def load(self, **kwargs):
        raise NotImplementedError()


class TrivialLoader(Loader):

    def load(self, **kwargs):
        return kwargs


class MetadataLoader(Loader):

    def load(self, file):
        return MetadataRepo(_load_q2_metadata(file, None))


constructors = {
    'AlphaQZALoader': TrivialLoader,
    'FeatureTableLoader': TrivialLoader,
    'TaxonomyDataLoader': TrivialLoader,
    'PCOALoader': TrivialLoader,
    'MetadataLoader': MetadataLoader,
    'TrivialLoader': TrivialLoader,
}

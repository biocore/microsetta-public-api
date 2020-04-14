class ModelBase:
    def _get_sample_ids(self):
        raise NotImplementedError

    def _get_feature_ids(self):
        raise NotImplementedError

    def sample_ids(self):
        return frozenset(self._get_sample_ids())

    def feature_ids(self):
        return frozenset(self._get_feature_ids())

    def get_group(self, ids, name=None):
        raise NotImplementedError

    def get_group_raw(self, ids=None, name=None):
        raise NotImplementedError

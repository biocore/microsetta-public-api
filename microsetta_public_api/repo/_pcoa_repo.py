from skbio.stats.ordination import OrdinationResults
from microsetta_public_api.resources import resources


class PCoARepo:

    def __init__(self, sample_sets=None):
        if sample_sets is None:
            sample_sets = resources.get('pcoa', dict())
        self._sample_sets = sample_sets

    def get_pcoa(self, sample_set, metric) -> OrdinationResults:
        return self._sample_sets[sample_set][metric]

    def has_pcoa(self, sample_set, metric):
        if sample_set not in self._sample_sets:
            return False
        else:
            return metric in self._sample_sets[sample_set]

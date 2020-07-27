from unittest import TestCase
from microsetta_public_api.resources import resources
from microsetta_public_api.repo._pcoa_repo import PCoARepo


_dne = object()


class PCoARepoTestCase(TestCase):

    def setUp(self) -> None:
        self.old_pcoa = resources.get('pcoa', _dne)
        resources['pcoa'] = {
            'some_sample_set': {
                'unifrac': 'unifrac_placeholder',
                'jaccard': 'jaccard_placeholder',
            },
            'other_set': {
                'unifrac': 'placeholder',
            }
        }

    def tearDown(self):
        if self.old_pcoa == _dne:
            del resources['pcoa']
        else:
            resources['pcoa'] = self.old_pcoa

    def test_get_pcoa(self):
        repo = PCoARepo()

        obs = repo.get_pcoa('some_sample_set', 'unifrac')
        self.assertEqual(obs, 'unifrac_placeholder')
        obs = repo.get_pcoa('other_set', 'unifrac')
        self.assertEqual(obs, 'placeholder')

    def test_has_pcoa(self):
        repo = PCoARepo()

        obs = repo.has_pcoa('some_sample_set', 'jaccard')
        self.assertTrue(obs)

        obs = repo.has_pcoa('some_sample_set', 'beta')
        self.assertFalse(obs)

        obs = repo.has_pcoa('dne_sample_set', 'beta')
        self.assertFalse(obs)

        obs = repo.has_pcoa('dne_sample_set', 'unifrac')
        self.assertFalse(obs)




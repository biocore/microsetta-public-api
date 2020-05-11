import unittest
from unittest.mock import patch
import pandas as pd
from qiime2 import Artifact
from pandas.testing import assert_series_equal

from microsetta_public_api import config
from microsetta_public_api.resources import resources
from microsetta_public_api.utils.testing import TempfileTestCase
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.exceptions import UnknownMetric


class TestAlphaRepoHelpers(TempfileTestCase):

    def test_load_resource_metric_not_available(self):
        alpha_repo = AlphaRepo()
        with patch.object(AlphaRepo, 'available_metrics') as mock_avail:
            mock_avail.return_value = ['faith_pd', 'chao1']
            with self.assertRaisesRegex(UnknownMetric, "No resource "
                                                       "available for "
                                                       "metric="
                                                       "'fake-test-metric'"):
                alpha_repo._get_resource('fake-test-metric')


class TestAlphaRepoWithResources(TempfileTestCase):

    def setUp(self):
        self.no_resources_repo = AlphaRepo()
        resource_filename1 = self.create_tempfile(suffix='.qza').name
        resource_filename2 = self.create_tempfile(suffix='.qza').name
        test_series1 = pd.Series({'sample1': 7.15, 'sample2': 9.04},
                                 name='chao1')
        test_series2 = pd.Series({'sample3': 7.24, 'sample2': 9.04,
                                  'sample4': 8.25},
                                 name='faith_pd')

        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", test_series1
        )
        imported_artifact.save(resource_filename1)

        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", test_series2
        )
        imported_artifact.save(resource_filename2)
        config.resources.update({
            'alpha_resources': {
                'chao1': resource_filename1,
                'faith_pd': resource_filename2,
            }
        })
        resources.update(config.resources)

        self.repo = AlphaRepo()

    def test_available_metrics(self):
        exp = ['chao1', 'faith_pd']
        obs = self.repo.available_metrics()
        self.assertCountEqual(exp, obs)

    def test_get_alpha_diversity(self):
        # group tests
        obs = self.repo.get_alpha_diversity(['sample2', 'sample1'], 'chao1')
        exp_series = pd.Series([9.04, 7.15], index=['sample2', 'sample1'],
                               name='chao1')
        assert_series_equal(obs, exp_series)

    def test_get_alpha_diversity_single_sample(self):
        # single sample tests
        obs = self.repo.get_alpha_diversity('sample2', 'chao1')
        exp_series = pd.Series([9.04], index=['sample2'],
                               name='chao1')
        assert_series_equal(obs, exp_series)

    def test_exists(self):
        # group tests
        sample_list = ['sample2', 'sample1', 'sample2', 'blah', 'sample4']
        obs = self.repo.exists(sample_list, 'chao1')
        exp = [True, True, True, False, False]
        self.assertListEqual(obs, exp)
        obs = self.repo.exists(sample_list, 'faith_pd')
        exp = [True, False, True, False, True]
        self.assertListEqual(obs, exp)

    def test_exists_single_sample(self):
        # single sample tests
        obs = self.repo.exists('sample1', 'chao1')
        self.assertTrue(obs)
        obs = self.repo.exists('sample1', 'faith_pd')
        self.assertFalse(obs)


if __name__ == '__main__':
    unittest.main()

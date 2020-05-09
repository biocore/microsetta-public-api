import pandas as pd
from pandas.util.testing import assert_series_equal
from qiime2 import Artifact
from q2_types.sample_data import SampleData, AlphaDiversity

from microsetta_public_api.exceptions import ConfigurationError
from microsetta_public_api.utils.testing import TempfileTestCase
from microsetta_public_api.resources import ResourceManager


class TestResourceManager(TempfileTestCase):

    def test_update(self):
        resources = ResourceManager(some_key='some_value')

        qza_resource_fp = self.create_tempfile(suffix='.qza').name
        qza_resource_fp2 = self.create_tempfile(suffix='.qza').name
        test_series = pd.Series({'sample1': 7.15, 'sample2': 9.04},
                                name='chao1')
        test_series2 = pd.Series({'sample1': 7.16, 'sample2': 9.01},
                                 name='faith_pd')
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", test_series
        )
        imported_artifact.save(qza_resource_fp)
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", test_series2
        )
        imported_artifact.save(qza_resource_fp2)

        update_with = {'random-value': 7.24,
                       'alpha_resources': {'chao1': qza_resource_fp,
                                           'faith_pd': qza_resource_fp2,
                                           },
                       'other': {'dict': {'of': 'things'}},
                       }
        resources.update(update_with)

        exp = {'some_key': 'some_value',
               'random-value': 7.24,
               'other': {'dict': {'of': 'things'}},
               }

        exp_alpha_resources = {'chao1': test_series,
                               'faith_pd': test_series2,
                               }
        self.assertIn('alpha_resources', resources)
        obs_alpha_resources = resources.pop('alpha_resources')
        self.assertDictEqual(resources, exp)
        self.assertListEqual(list(obs_alpha_resources.keys()),
                             ['chao1', 'faith_pd'])
        assert_series_equal(obs_alpha_resources['chao1'],
                            exp_alpha_resources['chao1'])
        assert_series_equal(obs_alpha_resources['faith_pd'],
                            exp_alpha_resources['faith_pd'])

    def test_update_bad_alpha_resources(self):
        resources = ResourceManager(some_key='some_value')

        qza_resource_fp = self.create_tempfile(suffix='.qza').name
        qza_resource_fh2 = self.create_tempfile(suffix='.qza')
        qza_resource_fp2 = qza_resource_fh2.name
        qza_resource_fh2.close()
        non_qza_resource_fp = self.create_tempfile(suffix='.some_ext').name
        test_series = pd.Series({'sample1': 7.15, 'sample2': 9.04},
                                name='chao1')
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", test_series
        )
        imported_artifact.save(qza_resource_fp)
        update_with = {'random-value': 7.24,
                       'alpha_resources': {'chao1': qza_resource_fp,
                                           'faith_pd': 9,
                                           },
                       'other': {'dict': {'of': 'things'}},
                       }
        with self.assertRaisesRegex(ValueError,
                                    'Expected existing path with .qza'):
            resources.update(update_with)

        with self.assertRaisesRegex(ValueError,
                                    'Expected existing path with .qza'):
            update_with['alpha_resources']['faith_pd'] = qza_resource_fp2
            resources.update(update_with)

        with self.assertRaisesRegex(ValueError,
                                    'Expected existing path with .qza'):
            update_with['alpha_resources']['faith_pd'] = non_qza_resource_fp
            resources.update(update_with)

        with self.assertRaisesRegex(ValueError,
                                    "Expected 'alpha_resources' field to "
                                    "contain a dict. Got int"):
            update_with['alpha_resources'] = 9
            resources.update(update_with)

    def test_parse_q2_data(self):
        resource_filename = self.create_tempfile(suffix='.qza').name
        test_series = pd.Series({'sample1': 7.15, 'sample2': 9.04},
                                name='chao1')
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", test_series
        )
        imported_artifact.save(resource_filename)

        res = ResourceManager()
        loaded_artifact = res._parse_q2_data(resource_filename,
                                             SampleData[AlphaDiversity])
        assert_series_equal(test_series, loaded_artifact)

    def test_parse_q2_data_wrong_semantic_type(self):
        resource_filename = self.create_tempfile(suffix='.qza').name
        test_series = pd.Series({'feature1': 'k__1', 'feature2': 'k__2'},
                                name='Taxon')
        test_series.index.name = 'Feature ID'
        imported_artifact = Artifact.import_data(
            # the distincion here is that this is not alpha diversity
            "FeatureData[Taxonomy]", test_series
        )
        imported_artifact.save(resource_filename)

        res = ResourceManager()
        with self.assertRaisesRegex(ConfigurationError,
                                    r"Expected (.*) "
                                    r"'SampleData\[AlphaDiversity\]'. "
                                    r"Received 'FeatureData\[Taxonomy\]'."):
            res._parse_q2_data(resource_filename, SampleData[AlphaDiversity])

    def test_parse_q2_data_file_does_not_exist(self):
        resource_file = self.create_tempfile(suffix='.qza')
        resource_filename = resource_file.name
        resource_file.close()

        res = ResourceManager()
        with self.assertRaisesRegex(ConfigurationError,
                                    r"does not exist"):
            res._parse_q2_data(resource_filename, SampleData[AlphaDiversity])

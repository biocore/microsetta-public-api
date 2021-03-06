import functools
import json
import types
import tempfile
from unittest.case import TestCase
from unittest.mock import patch
import pandas as pd
import numpy as np
import biom
from qiime2 import Metadata, Artifact


import microsetta_public_api
import microsetta_public_api.server
import microsetta_public_api.utils._utils
from microsetta_public_api import config
from microsetta_public_api.resources import resources
from microsetta_public_api.resources_alt import resources_alt
from microsetta_public_api.config import ConfigElementVisitor, Element


class MockMetadataElement(Element):

    def __init__(self, instance):
        super().__init__()
        self.instance = instance

    def accept(self, visitor):
        self.data = self.instance


class TrivialVisitor(ConfigElementVisitor):

    def visit(self, element):
        element.data = element

    visit_alpha = visit
    visit_taxonomy = visit
    visit_pcoa = visit
    visit_metadata = visit
    visit_beta = visit


class TempfileTestCase(TestCase):

    def setUp(self):
        self._tempfiles = []

    def create_tempfile(self, **named_temporary_file_kwargs):
        # See the docs here for kwargs:
        # https://docs.python.org/3/library/tempfile.html
        new_tempfile = tempfile.NamedTemporaryFile(
            **named_temporary_file_kwargs)
        self._tempfiles.append(new_tempfile)
        return new_tempfile

    def tearDown(self):
        for tempfile_ in self._tempfiles:
            tempfile_.close()


class FlaskTests(TestCase):

    def setUp(self):

        self.app, self.client = self.build_app_test_client()
        self.app_context = self.app.app.app_context

    @staticmethod
    def build_app_test_client():
        app = microsetta_public_api.server.build_app()
        client = app.app.test_client()
        return app, client

    def assertStatusCode(self, exp_code, response):
        try:
            status_code = response.status_code
            self.assertEqual(exp_code, status_code)
        except AssertionError:
            raise AssertionError(f'{exp_code} != {status_code}'
                                 f'\nRecieved response data: {response.data}')


def _copy_func(f, name=None):
    """
    Based on https://stackoverflow.com/q/13503079
    """
    g = types.FunctionType(f.__code__, f.__globals__, name or f.__name__,
                           argdefs=f.__defaults__, closure=f.__closure__)
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


class MockedResponse(str):

    def __init__(self, data):
        super().__init__()
        self.data = data

    def __eq__(self, other):
        if isinstance(other, MockedResponse):
            return self.data == other.data
        else:
            return self.data == other


def mocked_jsonify(*args, **kwargs):
    """Can be used to replace flask.jsonify, since it does not work
    outside of a application context

    From the flask docs:
        1. Single argument: Passed straight through to dumps
        2. Multiple arguments: converted to array and passed to dumps
        3. Multiple kwargs: converted to a dict and passed to dumps
        4. Both args and kwargs: behavior undefined and will throw an exception

    Additionally, a _MockedWebResponse object the
    """
    # need to return an object so its attributes can be set (like in get_alpha)
    def dump(data):
        return MockedResponse(json.dumps(data))
    if len(args) == 1 and len(kwargs) == 0:
        return dump(*args)
    elif len(args) > 1 and len(kwargs) == 0:
        return dump([arg for arg in args])
    elif len(args) == 0 and len(kwargs) > 0:
        return dump(kwargs)
    else:
        raise TypeError(f"mocked_jsonify got an unexpected combination of "
                        f"args and kwargs. Got args={args}, kwargs={kwargs}.")


class MockedJsonifyTestCase(TestCase):

    def setUp(self):
        if isinstance(self.jsonify_to_patch, str):
            self.jsonify_patcher = patch(
                self.jsonify_to_patch,
                new=mocked_jsonify,
            )
            self.mock_jsonify = self.jsonify_patcher.start()
        else:
            self.jsonify_patcher = [patch(jsonify_, new=mocked_jsonify) for
                                    jsonify_ in self.jsonify_to_patch]
            self.mock_jsonify = [patcher.start() for
                                 patcher in self.jsonify_patcher]

    def tearDown(self):
        if isinstance(self.mock_jsonify, list):
            for patcher in self.jsonify_patcher:
                patcher.stop()
        else:
            self.jsonify_patcher.stop()


class ConfigTestCase(TestCase):

    def setUp(self):
        self._config_copy = config.resources.copy()
        self._resources_copy = resources.copy()
        self._resources_alt_copy = resources_alt.copy()

    def tearDown(self):
        config.resources = self._config_copy
        resources.clear()
        dict.update(resources, self._resources_copy)
        resources_alt.clear()
        resources_alt.update(self._resources_alt_copy)


class TestDatabase:
    def __init__(self, n_samples=2000, seed=None):
        np.random.seed(seed)
        sample_set = [f'sample-{i + 1:04d}' for i in range(n_samples)]
        age_categories = np.array(['30s', '40s', '50s'])
        bmi_categories = np.array(['Normal', 'Overweight', 'Underweight'])

        self.faith_pd_data = pd.Series(np.random.normal(6, 1.5, n_samples),
                                       index=sample_set, name='faith_pd')

        self.taxonomy_greengenes_df = pd.DataFrame(
            [['feature-1', 'k__a; p__b; o__c', 0.123],
             ['feature-2', 'k__a; p__b; o__c; f__d; g__e', 0.34],
             ['feature-3', 'k__a; p__f; o__g; f__h', 0.678]],
            columns=['Feature ID', 'Taxon', 'Confidence'])
        self.taxonomy_greengenes_df.set_index('Feature ID', inplace=True)

        self.table = biom.Table(
            np.random.multinomial(5, [1/3.] * 3, size=n_samples).transpose(),
            ['feature-1', 'feature-2', 'feature-3'],
            sample_set)

        self.metadata_table = pd.DataFrame(
            {
                'age_cat': np.random.choice(age_categories,
                                            len(sample_set)),
                'bmi_cat': np.random.choice(bmi_categories,
                                            len(sample_set)),
            }, index=pd.Series(sample_set,
                               name='#SampleID')
        )

        self._tempfiles = []

    def create_tempfile(self, **named_temporary_file_kwargs):
        new_tempfile = tempfile.NamedTemporaryFile(
            **named_temporary_file_kwargs)
        self._tempfiles = []
        return new_tempfile

    def __enter__(self):
        self.start()

    def start(self):
        self.metadata_file = self.create_tempfile(suffix='.txt')
        metadata_path = self.metadata_file.name
        Metadata(self.metadata_table).save(metadata_path)
        self.faith_pd_file = self.create_tempfile(suffix='.qza')
        faith_pd_path = self.faith_pd_file.name
        faith_pd_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.faith_pd_data,
        )
        faith_pd_artifact.save(faith_pd_path)
        self.taxonomy_file = self.create_tempfile(suffix='.qza')
        taxonomy_path = self.taxonomy_file.name
        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy_greengenes_df
        )
        imported_artifact.save(taxonomy_path)
        self.table_file = self.create_tempfile(suffix='.qza')
        table_path = self.table_file.name
        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table
        )
        imported_artifact.save(table_path)
        config.resources.update({'metadata': metadata_path,
                                 'alpha_resources': {
                                     'faith-pd': faith_pd_path,
                                 },
                                 'table_resources': {
                                     'greengenes': {
                                         'table': table_path,
                                         'feature-data-taxonomy':
                                             taxonomy_path,
                                     }
                                 },
                                 })
        resources.update(config.resources)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stop()

    def stop(self):
        for file_ in self._tempfiles:
            file_.close()
        config.resources.clear()
        resources.clear()
        return True

import json
from unittest import mock
from microsetta_public_api.utils.testing import MockedJsonifyTestCase
from microsetta_public_api.api.datasets import available, dataset_detail


class DatasetsImplementationTests(MockedJsonifyTestCase):
    mock_resources = {
        'metadata': 'some/stuff/here',
        'datasets': {
            'shotgun': {
                '__taxonomy__': ['foo'],
                '__alpha__': ['bar'],
                '__dataset_detail__': {'title': 'foo'}
            },
            '16S': {
                '__pcoa__': {
                    'foo': 'bar',
                },
                '__dataset_detail__': {'title': 'bar'}
            },
            '__metadata__': '/path/to/md.txt',
        }
    }

    jsonify_to_patch = [
        'microsetta_public_api.api.datasets.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def test_datasets_available(self):
        with mock.patch('microsetta_public_api.api.datasets.get_resources') \
                as mock_get_resources:
            mock_get_resources.return_value = self.mock_resources
            response, code = available()

        exp = {'shotgun': {'title': 'foo'},
               '16S': {'title': 'bar'}}
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertEqual(obs, exp)

    def test_specific_dataset_exists(self):
        with mock.patch('microsetta_public_api.api.datasets.get_resources') \
                as mock_get_resources:
            mock_get_resources.return_value = self.mock_resources
            response, code = dataset_detail('16S')

        exp = {'16S': {'title': 'bar'}}
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertEqual(obs, exp)

    def test_specific_dataset_missing(self):
        with mock.patch('microsetta_public_api.api.datasets.get_resources') \
                as mock_get_resources:
            mock_get_resources.return_value = self.mock_resources
            response, code = dataset_detail('foobar')

        self.assertEqual(code, 404)

    def test_datasets_available_none(self):
        mock_resources = {
            'metadata': 'some/stuff/here',
            'datasets': {
                '__metadata__': '/path/to/md.txt',
            }
        }
        with mock.patch('microsetta_public_api.api.datasets.get_resources') \
                as mock_get_resources:
            mock_get_resources.return_value = mock_resources
            response, code = available()

        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertCountEqual([], obs)

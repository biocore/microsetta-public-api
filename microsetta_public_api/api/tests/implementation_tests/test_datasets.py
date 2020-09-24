import json
from unittest import mock
from microsetta_public_api.utils.testing import MockedJsonifyTestCase
from microsetta_public_api.api.datasets import available


class DatasetsImplementationTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.datasets.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def test_datasets_available(self):
        mock_resources = {
            'metadata': 'some/stuff/here',
            'datasets': {
                'shotgun': {
                    '__taxonomy__': ['foo'],
                    '__alpha__': ['bar'],
                },
                '16S': {
                    '__pcoa__': {
                        'foo': 'bar',
                    }
                },
                '__metadata__': '/path/to/md.txt',
            }
        }
        with mock.patch('microsetta_public_api.api.datasets.get_resources') \
                as mock_get_resources:
            mock_get_resources.return_value = mock_resources
            response, code = available()

        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertCountEqual(['shotgun', '16S'], obs)

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

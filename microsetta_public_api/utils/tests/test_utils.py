from unittest.case import TestCase

from microsetta_public_api.utils.testing import mocked_jsonify, TestDatabase
from microsetta_public_api.resources import resources


class MockedJsonifyTests(TestCase):

    def test_mock_jsonify(self):
        mocked_jsonify('a')
        mocked_jsonify(a='a', b='b')
        mocked_jsonify('a', 'b', 'c')
        with self.assertRaises(TypeError):
            mocked_jsonify({'a': 'b', 'c': 'd'}, e='f')


class TestDatabaseTests(TestCase):

    def test_basic_test_db(self):
        with TestDatabase():
            self.assertIn('metadata', resources)
            self.assertIn('alpha_resources', resources)

        self.assertNotIn('metadata', resources)
        self.assertNotIn('alpha_resources', resources)

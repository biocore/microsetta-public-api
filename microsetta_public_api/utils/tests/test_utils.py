from unittest.case import TestCase

from microsetta_public_api.utils.testing import mocked_jsonify


class MockedJsonifyTests(TestCase):

    def test_mock_jsonify(self):
        mocked_jsonify('a')
        mocked_jsonify(a='a', b='b')
        mocked_jsonify('a', 'b', 'c')
        with self.assertRaises(TypeError):
            mocked_jsonify({'a': 'b', 'c': 'd'}, e='f')

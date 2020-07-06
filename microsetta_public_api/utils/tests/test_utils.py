from unittest.case import TestCase

from microsetta_public_api.utils.testing import mocked_jsonify
from microsetta_public_api.utils import DataTable, create_data_entry
import json
import pandas as pd


class MockedJsonifyTests(TestCase):

    def test_mock_jsonify(self):
        mocked_jsonify('a')
        mocked_jsonify(a='a', b='b')
        mocked_jsonify('a', 'b', 'c')
        with self.assertRaises(TypeError):
            mocked_jsonify({'a': 'b', 'c': 'd'}, e='f')


class TestDataTable(TestCase):

    def test_data_entry(self):
        DataEntry = create_data_entry(['foo', 'bar'])
        obs = DataEntry(foo='baz', bar='qux')
        exp = {'foo': 'baz', 'bar': 'qux'}
        self.assertDictEqual(exp, obs.to_dict())

    def test_data_table(self):
        DataEntry = create_data_entry(['foo', 'bar'])
        entry1 = DataEntry(foo='baz', bar='qux')
        entry2 = DataEntry(foo='quuz', bar='corge')

        dt = DataTable(data=[entry1, entry2], columns=['foo', 'bar'])
        obs_dict = dt.to_dict()
        exp_dict = {'data': [{'foo': 'baz', 'bar': 'qux'}, {'foo': 'quuz',
                                                            'bar': 'corge'}],
                    'columns': ['foo', 'bar'],
                    }

        obs = json.dumps(obs_dict)
        exp = json.dumps(exp_dict)
        self.assertEqual(obs, exp)

    def test_data_table_from_dataframe(self):
        dict_ = {'data': [{'foo': 'baz', 'bar': 'qux'}, {'foo': 'quuz',
                                                         'bar': 'corge'}],
                 'columns': ['foo', 'bar'],
                 }
        df = pd.DataFrame(dict_['data'], columns=dict_['columns'])

        dt = DataTable.from_dataframe(df)

        dict_['columns'] = [{'data': 'foo'}, {'data': 'bar'}]

        obs_dict = dt.to_dict()
        obs = json.dumps(obs_dict)
        exp = json.dumps(dict_)
        self.assertEqual(obs, exp)

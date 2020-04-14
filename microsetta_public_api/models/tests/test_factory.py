import unittest
import pandas as pd
import pandas.testing as pdt

from microsetta_public_api.models._factory import AlphaFactory
from microsetta_public_api.models._exceptions import UnknownID
# from microsetta_public_api.models._util import OTU


class MockAlphaResource:
    def get_alpha(self):
        df = pd.DataFrame([('1', 2, 3),
                           ('x', 3, 4),
                           ('y', 7, 8)], columns=['sample-id', 'foo', 'bar'])
        return df.set_index('sample-id')


# class MockTaxonomyResource:
#     def get_taxonomy(self):
#         tree = skbio.TreeNode.read(["((a,b)c,(d,e)f)root;"])
#         structure = {'1': (OTU(node=tree.find('a'), value=0.4),
#                            OTU(node=tree.find('e'), value=0.6)),
#                      'x': (OTU(node=tree.find('c'), value=1.), ),
#                      'y': (OTU(node=tree.find('d'), value=0.2),
#                            OTU(node=tree.find('e'), value=0.8))}
#         return structure


class AlphaFactoryTests(unittest.TestCase):
    def setUp(self):
        self.resource = MockAlphaResource()
        self.factory = AlphaFactory(self.resource)

    def test_collection(self):
        f = self.factory.collection()
        self.assertEqual(f(), ['foo', 'bar'])

    def test_samples(self):
        f = self.factory.samples()
        exp = pd.DataFrame([('x', 3, 4),
                            ('y', 7, 8)], columns=['sample-id', 'foo', 'bar'])
        exp.set_index('sample-id', inplace=True)
        obs = f(['x', 'y'])
        pdt.assert_frame_equal(obs, exp)

    def test_samples_bad_id(self):
        f = self.factory.samples()
        with self.assertRaisesRegex(UnknownID, "baz"):
            f(['baz', ])


# class TaxonomyFactoryTests(unittest.TestCase):
#     def setUp(self):
#         self.resource = MockTaxonomyResource()
#         self.factory = TaxonomyFactory(self.resource)
#
#     def test_collection(self):
#         f = self.factory.collection()
#         exp = "((a,b)c,(d,e)f)root;"
#         obs = f()
#         self.assertEqual(obs, exp)
#
#     def test_samples(self):
#         f = self.factory.samples()
#         exp = {'1': "(('a%%%0.4')c,('e%%%0.6')f)root;",
#                'x': "('c%%%1.')root;",
#                'y': "(('d%%%0.2','e%%%0.8')f)root;"}
#         obs = f()
#         self.assertEqual(obs, exp)


if __name__ == '__main__':
    unittest.main()

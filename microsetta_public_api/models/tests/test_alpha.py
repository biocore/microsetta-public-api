import unittest
import pandas as pd
import pandas.testing as pdt
import numpy.testing as npt

from microsetta_public_api.models._exceptions import UnknownID
from microsetta_public_api.models._alpha import GroupAlpha, Alpha, \
    GroupAlphaRaw


class AlphaTests(unittest.TestCase):
    def setUp(self):
        self.series = pd.Series([0.1, 0.2, 0.8, 0.7, 0.7, 0.6],
                                index=['a', 'b', 'c', 'd', 'e', 'f'],
                                name='shannon')

    def test_init(self):
        adiv = Alpha(self.series)
        pdt.assert_series_equal(adiv._series, self.series)

    def test_sample_ids(self):
        adiv = Alpha(self.series)
        self.assertEqual(adiv.sample_ids(),
                         frozenset({'a', 'b', 'c', 'd', 'e', 'f'}))

    def test_feature_ids(self):
        adiv = Alpha(self.series)
        self.assertEqual(adiv.feature_ids(), frozenset())

    def test_get_group_single(self):
        adiv = Alpha(self.series)
        exp = GroupAlpha(name='b',
                         alpha_metric='shannon',
                         mean=0.2,
                         median=0.2,
                         std=0.0,
                         group_size=1,
                         percentile=None,
                         percentile_values=None)
        obs = adiv.get_group(['b'])
        self.assertEqual(obs, exp)

    def test_get_group_multi(self):
        adiv = Alpha(self.series)
        exp = GroupAlpha(name='bar',
                         alpha_metric='shannon',
                         mean=0.35,
                         median=0.35,
                         std=0.25,
                         group_size=2,
                         percentile=[10, 20, 30, 40, 50, 60, 70, 80, 90],
                         percentile_values=[0.15, 0.2, 0.25, 0.3, 0.35, 0.4,
                                            0.45, 0.5, 0.55])
        obs = adiv.get_group(['a', 'f'], 'bar')
        self.assertEqual(obs.name, exp.name)
        self.assertEqual(obs.alpha_metric, exp.alpha_metric)
        self.assertAlmostEqual(obs.mean, exp.mean)
        self.assertAlmostEqual(obs.median, exp.median)
        self.assertAlmostEqual(obs.std, exp.std)
        self.assertEqual(obs.group_size, exp.group_size)
        npt.assert_equal(obs.percentile, exp.percentile)
        npt.assert_almost_equal(obs.percentile_values, exp.percentile_values)

    def test_get_group_missing(self):
        adiv = Alpha(self.series)
        with self.assertRaisesRegex(UnknownID, "Identifier not found."):
            adiv.get_group(['foobarbaz'], 'asd')

    def test_get_group_noname(self):
        adiv = Alpha(self.series)
        with self.assertRaises(ValueError):
            adiv.get_group(['a', 'b'])

    def test_get_group_raw(self):
        adiv = Alpha(self.series)
        self.series = pd.Series([0.1, 0.2, 0.8, 0.7, 0.7, 0.6],
                                index=['a', 'b', 'c', 'd', 'e', 'f'],
                                name='shannon')
        exp_all = GroupAlphaRaw(name=None,
                                alpha_metric='shannon',
                                alpha_diversity={'a': 0.1, 'b': 0.2, 'c': 0.8,
                                                 'd': 0.7, 'e': 0.7, 'f': 0.6})
        obs_all = adiv.get_group_raw()
        self.assertEqual(obs_all, exp_all)

        exp_partial = GroupAlphaRaw(name='foo',
                                    alpha_metric='shannon',
                                    alpha_diversity={'a': 0.1, 'c': 0.8,
                                                     'f': 0.6})
        obs_partial = adiv.get_group_raw(['a', 'c', 'f'], 'foo')
        self.assertEqual(obs_partial, exp_partial)

    def test_get_group_raw_missing(self):
        adiv = Alpha(self.series)
        with self.assertRaisesRegex(UnknownID, "Identifier not found."):
            adiv.get_group_raw(['foo', 'bar'], 'baz')

    def test_get_group_raw_noname(self):
        adiv = Alpha(self.series)
        with self.assertRaisesRegex(ValueError, "Name not specified."):
            adiv.get_group_raw(['a', 'c'])


class GroupAlphaRawTests(unittest.TestCase):
    def setUp(self):
        self.obj = GroupAlphaRaw(name=None,
                                 alpha_metric='shannon',
                                 alpha_diversity={'a': 10, 'b': 20})
        self.obj2 = GroupAlphaRaw(name='foobar',
                                  alpha_metric='shannon',
                                  alpha_diversity={'a': 10, 'b': 20, 'c': 30})

    def test_init(self):
        self.assertEqual(self.obj.name, None)
        self.assertEqual(self.obj.alpha_metric, 'shannon')
        self.assertEqual(self.obj.alpha_diversity, {'a': 10, 'b': 20})

    def test_init_nokw(self):
        with self.assertRaises(NotImplementedError):
            GroupAlphaRaw('foo', 'bar', 'baz')


class GroupAlphaTests(unittest.TestCase):
    def setUp(self):
        self.obj = GroupAlpha(name='sample-1',
                              alpha_metric='shannon',
                              mean=0.2,
                              median=0.2,
                              std=0.0,
                              group_size=1,
                              percentile=None,
                              percentile_values=None)

        self.obj2 = GroupAlpha(name='abx-low',
                               alpha_metric='faiths',
                               mean=0.5,
                               median=0.4,
                               std=0.1,
                               group_size=100,
                               percentile=[25, 50, 75],
                               percentile_values=[0.2, 0.4, 0.6])

    def test_init(self):
        self.assertEqual(self.obj.name, 'sample-1')
        self.assertEqual(self.obj.alpha_metric, 'shannon')
        self.assertEqual(self.obj.mean, 0.2)
        self.assertEqual(self.obj.median, 0.2)
        self.assertEqual(self.obj.std, 0.0)
        self.assertEqual(self.obj.group_size, 1)
        self.assertEqual(self.obj.percentile, None)
        self.assertEqual(self.obj.percentile_values, None)

    def test_init_group_size_lte_0(self):
        with self.assertRaisesRegex(ValueError, "bad group_size."):
            GroupAlpha(name='abx-low',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.1,
                       group_size=0,
                       percentile=[25, 50, 75, 90],
                       percentile_values=[0.2, 0.4, 0.6])

    def test_init_group_size_gt_1(self):
        with self.assertRaisesRegex(ValueError, "unmatched percentiles."):
            GroupAlpha(name='abx-low',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.1,
                       group_size=100,
                       percentile=[25, 50, 75, 90],
                       percentile_values=[0.2, 0.4, 0.6])

        with self.assertRaisesRegex(ValueError, "unmatched percentiles."):
            GroupAlpha(name='abx-low',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.1,
                       group_size=100,
                       percentile=[25, 50, 75],
                       percentile_values=[0.2, 0.4, 0.6, 0.8])

        with self.assertRaisesRegex(ValueError, "Missing percentiles."):
            GroupAlpha(name='abx-low',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.1,
                       group_size=100,
                       percentile=None,
                       percentile_values=[0.2, 0.4, 0.6, 0.8])

        with self.assertRaisesRegex(ValueError, "Missing percentiles."):
            GroupAlpha(name='abx-low',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.1,
                       group_size=100,
                       percentile=[25, 50, 75],
                       percentile_values=None)

        with self.assertRaisesRegex(ValueError, "Missing percentiles."):
            GroupAlpha(name='abx-low',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.1,
                       group_size=100,
                       percentile=None,
                       percentile_values=None)

    def test_init_group_size_1(self):
        with self.assertRaisesRegex(ValueError, "non-sensical for n=1."):
            GroupAlpha(name='sample-1',
                       alpha_metric='faiths',
                       mean=0.4,
                       median=0.5,
                       std=0.0,
                       group_size=1,
                       percentile=None,
                       percentile_values=None)

        with self.assertRaisesRegex(ValueError, "non-sensical for n=1."):
            GroupAlpha(name='sample-1',
                       alpha_metric='faiths',
                       mean=0.5,
                       median=0.4,
                       std=0.0,
                       group_size=1,
                       percentile=None,
                       percentile_values=None)

        with self.assertRaisesRegex(ValueError, "non-sensical for n=1."):
            GroupAlpha(name='sample-1',
                       alpha_metric='faiths',
                       mean=0.4,
                       median=0.4,
                       std=0.0,
                       group_size=1,
                       percentile=[50, ],
                       percentile_values=[0.4, ])

    def test_to_dict(self):
        exp = {'name': 'abx-low',
               'alpha_metric': 'faiths',
               'mean': 0.5,
               'median': 0.4,
               'std': 0.1,
               'group_size': 100,
               'percentile': [25, 50, 75],
               'percentile_values': [0.2, 0.4, 0.6]}
        obs = self.obj2.to_dict()
        self.assertEqual(obs, exp)

        exp = {'name': 'sample-1',
               'alpha_metric': 'shannon',
               'mean': 0.2,
               'median': 0.2,
               'std': 0.0,
               'group_size': 1,
               'percentile': None,
               'percentile_values': None}
        obs = self.obj.to_dict()
        self.assertEqual(obs, exp)

    def test_str(self):
        obs = str(self.obj)
        exp = str(self.obj.to_dict())
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    unittest.main()

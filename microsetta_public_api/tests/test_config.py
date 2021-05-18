from unittest import TestCase
from unittest.mock import MagicMock
import json
import copy
from jsonschema.exceptions import ValidationError
from microsetta_public_api.config import (
    Element,
    AlphaElement,
    BetaElement,
    NeighborsElement,
    MetadataElement,
    DictElement,
    PCOAElement,
    DatasetDetailElement,
    TaxonomyElement,
    ConfigElementVisitor,
    SchemaBase,
    Schema,
    CompatibilitySchema,
)


class TestConfigSchema(TestCase):
    def test_validate_new_schema(self):
        test_config = {
            'datasets': {
                '16SAmplicon':
                {
                    '__alpha__': {
                        'faith_pd': '/path/to/faith_pd.qza',
                        'shannon': '/path/to/shannon.qza',
                    },
                    '__taxonomy__': {
                        'agp': {
                            'table': '/path/to/table.qza',
                            'feature-data-taxonomy': '/path/to/tax.qza',
                        },
                        'agp-collapsed': {
                            'table': '/path/2/table.qza',
                            'feature-data-taxonomy': '/path/2/tax.qza',
                        },
                    },
                    '__pcoa__': {
                        'oral': {
                            'unifrac': '/path/to/oral_unifrac.qza',
                            'braycurtis': '/path/to/oral_bc.qza',
                        },
                        'all': {
                            'unifrac': '/path/to/all_unifrac.qza',
                        }
                    },
                    '__beta__': {
                        'unifrac': '/path/to/unifrac.qza',
                        'braycurtis': '/path/to/braycurtis.qza',
                    },
                    '__neighbors__': {
                        'unifrac': '/path/to/unifrac.qza',
                        'braycurtis': '/path/to/braycurtis.qza',
                    },
                    '__metadata__': '/path/to/metadata.tsv',
                    '__dataset_detail__': {
                        'title': 'foobar',
                        'qiita-study-ids': ['foo', 'bar'],
                        'datatype': '16S'
                    },
                },
                'ShotgunMetagenomics': {
                    '__alpha__': {
                        'faith_pd': 'path/to/shotgun_faith_pd.qza'
                    },
                    '__metadata__': '/path/to/metadata.tsv',
                    '__dataset_detail__': {
                        'title': 'baz',
                        'qiita-study-ids': ['foo', 'bar'],
                        'datatype': 'WGS'
                    },
                },
            },
        }
        # will throw an exception if its wrong
        Schema().validate(instance=test_config)

    def test_compatibility_schema(self):
        test_config = {
            'datasets': {
                '16SAmplicon': {
                    '__alpha__': {
                        'faith_pd': '/path/to/faith_pd.qza',
                        'shannon': '/path/to/shannon.qza',
                    },
                    '__taxonomy__': {
                        'agp': {
                            'table': '/path/to/table.qza',
                            'feature-data-taxonomy': '/path/to/tax.qza',
                        },
                        'agp-collapsed': {
                            'table': '/path/2/table.qza',
                            'feature-data-taxonomy': '/path/2/tax.qza',
                        },
                    },
                    '__pcoa__': {
                        'oral': {
                            'unifrac': '/path/to/oral_unifrac.qza',
                            'braycurtis': '/path/to/oral_bc.qza',
                        },
                        'all': {
                            'unifrac': '/path/to/all_unifrac.qza',
                        }
                    },
                },
                'ShotgunMetagenomics': {
                    '__alpha__': {
                        'faith_pd': 'path/to/shotgun_faith_pd.qza',
                    },
                    '__neighbors__': {
                        'unifrac': '/path/to/unifrac.qza',
                        'braycurtis': '/path/to/braycurtis.qza',
                    },
                    '__metadata__': '/path/to/metadata.tsv',
                },
                '__metadata__': '/path/to/metadata.tsv',
            },
            'alpha_resources': {
                'faith_pd': '/path/to/faith_pd.qza',
                'shannon': '/path/to/shannon.qza',
            },
            'table_resources': {
                'agp': {
                    'table': '/path/to/table.qza',
                    'feature-data-taxonomy': '/path/to/tax.qza',
                },
            },
            'pcoa': {
                'oral': {
                    'unifrac': '/path/to/oral_unifrac.qza',
                },
            },
            'metadata': "somefilepath",

        }
        # will throw an exception if its wrong
        schema = CompatibilitySchema()
        schema.validate(instance=test_config)
        parsed_config = schema.make_elements(test_config)
        obs = parsed_config.gets('metadata')
        self.assertIsInstance(obs, MetadataElement)
        obs = parsed_config.gets('datasets', '__metadata__')
        self.assertIsInstance(obs, MetadataElement)

        test_config['alpha_resources'] = 'some string'
        with self.assertRaises(ValidationError):
            schema.validate(instance=test_config)

    def test_valdiate_new_schema_wrong(self):
        test_config = {
            'datasets': {
                '16SAmplicon':
                    {
                        '__alpha__': {
                            'faith_pd': '/path/to/faith_pd.qza',
                            'shannon': '/path/to/shannon.qza',
                        },
                        '__taxonomy__': {
                            'agp': {
                                'table': '/path/to/table.qza',
                                'feature-data-taxonomy': '/path/to/tax.qza',
                            },
                            'agp-collapsed': {
                                'table': '/path/2/table.qza',
                                'feature-data-taxonomy': '/path/2/tax.qza',
                            },
                        },
                        '__pcoa__': {
                            'oral': {
                                'unifrac': '/path/to/oral_unifrac.qza',
                                'braycurtis': '/path/to/oral_bc.qza',
                            },
                            'all': {
                                'unifrac': '/path/to/all_unifrac.qza',
                            }
                        },
                    },
                'ShotgunMetagenomics': {
                    '__alpha__': {
                        'faith_pd': 'path/to/shotgun_faith_pd.qza',
                    },
                    # this validates that adding an extra keyword to a
                    # dataset will make it invalid
                    '__bad_kw__': [
                        'anything'
                    ],
                    },
            },
            '__metadata__': '/path/to/metadata.tsv',
        }
        # will throw an exception if its wrong
        with self.assertRaises(ValidationError):
            Schema().validate(instance=test_config)


class TestParsing(TestCase):

    def test_json_hook(self):
        config = {
            "dataset": {
                "__alpha__": {
                    "a": "b",
                    "__taxonomy__": {
                        "a": [{"a": {"__pcoa__": {"do": "this"}}}],
                    }
                },
                "__metadata__": "/some/path",
            }
        }
        dict_config = json.loads(json.dumps(config))
        parsed_config = SchemaBase().make_elements(dict_config)
        self.assertIsInstance(parsed_config['dataset']['__alpha__'],
                              AlphaElement)
        self.assertIsInstance(parsed_config['dataset']['__metadata__'],
                              MetadataElement)
        self.assertIsInstance(parsed_config['dataset'], DictElement)
        self.assertEqual(parsed_config['dataset']['__metadata__'],
                         '/some/path')
        obs = parsed_config['dataset']['__alpha__']['__taxonomy__']["a"][0][
            "a"]["__pcoa__"]
        self.assertIsInstance(obs, PCOAElement)
        obs = parsed_config['dataset']['__alpha__']['__taxonomy__']
        self.assertIsInstance(obs, TaxonomyElement)
        self.assertIsInstance(parsed_config, Element)

        old_metadata_id = id(parsed_config['dataset']['__metadata__'])
        new_metadata_id = id(copy.copy(parsed_config)['dataset']
                             ['__metadata__'])
        self.assertEqual(old_metadata_id, new_metadata_id)

        copied_config = copy.deepcopy(parsed_config)
        self.assertIsInstance(copied_config['dataset']['__alpha__'],
                              AlphaElement)
        self.assertIsInstance(copied_config['dataset']['__metadata__'],
                              MetadataElement)
        new_metadata_id = id(copied_config['dataset']['__metadata__'])
        self.assertNotEqual(old_metadata_id, new_metadata_id)

        mock = MagicMock()
        copied_config['dataset']['__alpha__'].accept(mock)
        mock.visit_alpha.assert_called()
        mock2 = MagicMock()
        copied_config.accept(mock2)
        mock2.visit_alpha.assert_called()
        mock2.visit_pcoa.assert_called()
        mock2.visit_taxonomy.assert_called()

    def test_has(self):
        config = {
            "dataset": {
                "__alpha__": {
                    "a": "b",
                    "__taxonomy__": {
                        "a": [{"a": {"__pcoa__": {"do": "this"}}}],
                    }
                },
                "__metadata__": "/some/path",
                "other": 9,
            }
        }
        # parsed_config = json.loads(json.dumps(config), object_hook=as_config)
        parsed_config = SchemaBase().make_elements(
            json.loads(json.dumps(config)))
        obs = parsed_config.has('dataset', '__alpha__', '__taxonomy__',
                                'a', 0, 'a', '__pcoa__')
        self.assertTrue(obs)
        obs = parsed_config.has('dataset', '__metadata__', '/some/path')
        self.assertFalse(obs)
        obs = parsed_config.has('dataset', '__alpha__', '__taxonomy__', 'a')
        self.assertTrue(obs)
        obs = parsed_config.has('dataset', '__alpha__', '__taxonomy__', 'a', 8)
        self.assertFalse(obs)
        obs = parsed_config.has('dataset', '__alpha__', '__taxonomy__', 'a',
                                'go-fish')
        self.assertFalse(obs)
        obs = parsed_config.has('dataset', 'other')
        self.assertTrue(obs)
        obs = parsed_config.has('dataset', 'other', 9)
        self.assertFalse(obs)
        obs = parsed_config.has('dataset', 'other', 9, 19)
        self.assertFalse(obs)

    def test_make_elements_with_alternate_schema(self):
        class AlternateSchema(SchemaBase):
            def __init__(self):
                self.alpha_kw = '__foo__'
                self.taxonomy_kw = '__bar__'
                self.pcoa_kw = '__alpha__'
                self.metadata_kw = '__qux__'
                self.beta_kw = '__corge__'
                self.detail_kw = '__okay__'
                self.neighbors_kw = '__whatisthis__'

        self.assertDictEqual(AlternateSchema().element_map(),
                             {"__foo__": AlphaElement,
                              "__bar__": TaxonomyElement,
                              "__alpha__": PCOAElement,
                              "__qux__": MetadataElement,
                              "__corge__": BetaElement,
                              "__okay__": DatasetDetailElement,
                              '__whatisthis__': NeighborsElement
                              })

        config = {
            "datasets": {
                "__alpha__": {
                    "a": "b",
                    "__taxonomy__": {
                        "a": [{"a": {"__pcoa__": {"do": "this"}}}],
                    }
                },
                "__metadata__": "/some/path",
            }
        }
        schema = AlternateSchema()
        loaded_config = json.loads(json.dumps(config))
        parsed_config = schema.make_elements(loaded_config)
        obs = parsed_config.gets('datasets', '__alpha__')
        self.assertIsInstance(obs, PCOAElement)
        obs = parsed_config.gets('datasets', '__metadata__')
        self.assertNotIsInstance(obs, MetadataElement)

    def test_gets(self):
        config = {
            "dataset": {
                "__alpha__": {
                    "a": "b",
                    "__taxonomy__": {
                        "a": [{"a": {"__pcoa__": {"do": "this"}}}],
                    }
                },
                "__metadata__": "/some/path",
                "other": 9,
            }
        }
        parsed_config = SchemaBase().make_elements(json.loads(json.dumps(
            config)))
        obs = parsed_config.gets('dataset', '__alpha__', '__taxonomy__',
                                 'a', 0, 'a', '__pcoa__')
        self.assertDictEqual(obs, {"do": "this"})
        with self.assertRaises(KeyError):
            parsed_config.gets('dataset', '__metadata__', '/some/path')
        obs = parsed_config.gets('dataset', '__alpha__', '__taxonomy__', 'a')
        self.assertEqual([{"a": {"__pcoa__": {"do": "this"}}}], obs)
        with self.assertRaises(KeyError):
            parsed_config.gets('dataset', '__alpha__', '__taxonomy__',
                               'a', 8)
        with self.assertRaises(KeyError):
            parsed_config.gets('dataset', '__alpha__', '__taxonomy__', 'a',
                               'go-fish')
        obs = parsed_config.gets('dataset', 'other')
        self.assertEqual(obs, 9)
        with self.assertRaises(KeyError):
            parsed_config.gets('dataset', 'other', 9)
        with self.assertRaises(KeyError):
            parsed_config.gets('dataset', 'other', 9, 19)

    def test_deep_list_config(self):
        config = [[[[[{'__metadata__': 'filepath'}, {}]]]]]
        parsed_config = SchemaBase().make_elements(
            json.loads(json.dumps(config)))
        self.assertIsInstance(parsed_config, Element)
        self.assertIsInstance(parsed_config[0], Element)
        self.assertIsInstance(parsed_config[0][0], Element)
        self.assertIsInstance(parsed_config[0][0][0][0][0], Element)
        self.assertIsInstance(parsed_config[0][0][0][0][0]['__metadata__'],
                              MetadataElement)


class TestElement(TestCase):

    def test_nested_element(self):
        element = AlphaElement(DictElement({'a': 'b',
                                            'c': MetadataElement('d')}))
        mock = MagicMock()
        element.accept(mock)
        mock.visit_alpha.assert_called()
        mock.visit_metadata.assert_called()

    def test_updates(self):
        element = DictElement({'a': DictElement({'b': None})})
        element.updates(MetadataElement('Arg'), 'a', 'b')
        self.assertEqual('Arg', element.gets('a', 'b'))

        element.updates('Arg2', 'a', 'b', 'c', 'd', 'e')
        self.assertEqual('Arg2', element.gets('a', 'b', 'c', 'd', 'e'))
        element.updates('Arg3', 'c', 'd')
        self.assertEqual('Arg3', element['c']['d'])

        element.updates(DictElement({'a': DictElement({'c': MetadataElement(
            'Arg4')
        })}))
        self.assertEqual('Arg3', element['c']['d'])
        self.assertEqual('Arg4', element['a']['c'])

        exp = {'bar': {'qux': 'corge', 'hoge': 'piyo'}}
        foo = DictElement({'bar': DictElement({'qux': 'corge'})})
        foo.updates('piyo', 'bar', 'hoge')
        self.assertDictEqual(exp, foo)
        foo = DictElement({'bar': DictElement({'qux': 'corge'})})
        foo.updates({'bar': DictElement({'hoge': 'piyo'})})
        self.assertDictEqual(exp, foo)
        exp = {'bar': {'qux': 'corge', 'hoge': 'fuga'}}
        foo.updates('fuga', 'bar', 'hoge')
        self.assertDictEqual(exp, foo)
        foo.updates('waldo', 'bar', 'garp', 'grault')
        exp = {'bar': {'qux': 'corge', 'hoge': 'fuga',
                       'garp': {'grault': 'waldo'}}}
        self.assertDictEqual(exp, foo)
        foo = DictElement()
        foo.updates({'datasets': {'garply': 'grault'}})
        self.assertDictEqual({'datasets': {'garply': 'grault'}}, foo)

        foo = DictElement()
        foo.updates({'datasets': AlphaElement({'garply': 'grault'})})
        self.assertDictEqual({'datasets': {'garply': 'grault'}}, foo)
        self.assertIsInstance(foo['datasets'], AlphaElement)

    # TODO this should probably have more tests...


class TestVisiting(TestCase):

    def test_visitation(self):

        element = AlphaElement({
            'foo': TaxonomyElement({
                'bar': PCOAElement({
                    'baz': MetadataElement('path to stuff!'),
                    'bart': PCOAElement({'a': 'b'})
                })
            })
        })

        class MockVisitor(ConfigElementVisitor):
            def visit_alpha(self, element):
                element.data = 725

            def visit_taxonomy(self, element):
                element.data = 'taxonomy!'

            def visit_pcoa(self, element):
                element.data = element.copy()
                element.data.update({'c': 'cookie'})

            def visit_metadata(self, element):
                element.data = ConfigElementVisitor

        element.accept(MockVisitor())

        self.assertEqual(element.gets().data, 725)
        self.assertEqual(element.gets('foo').data, 'taxonomy!')
        first_pcoa = element.gets('foo', 'bar')
        self.assertDictEqual(first_pcoa.data,
                             {'baz': MetadataElement('path to stuff!'),
                              'bart': PCOAElement({'a': 'b'}),
                              'c': 'cookie',
                              }
                             )
        self.assertEqual(element.gets('foo', 'bar', 'baz').data,
                         ConfigElementVisitor
                         )
        metadata = element.gets('foo', 'bar', 'baz').data
        self.assertEqual(metadata, ConfigElementVisitor)
        self.assertDictEqual(element.gets('foo', 'bar', 'bart').data,
                             {'a': 'b',
                              'c': 'cookie'}
                             )

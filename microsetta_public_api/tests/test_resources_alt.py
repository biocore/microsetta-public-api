from unittest import TestCase
from unittest.mock import patch, Mock

from microsetta_public_api.resources_alt import Component


class ComponentTests(TestCase):

    def test_init(self):
        comp = Component('some_name')
        self.assertEqual(comp.name, 'some_name')
        self.assertDictEqual(comp.children, dict())
        self.assertIsNone(comp.data)
        self.assertIsNone(comp.parent)

    def test_add_child(self):
        comp = Component('some_name')
        child1 = Component('child1')
        child2 = Component('child2')
        child3 = Component('child3')
        comp.add_child(child1)
        child1.add_child(child2)
        child1.add_child(child3)
        self.assertDictEqual(comp.children,
                             {'child1': child1}
                             )
        self.assertDictEqual(child1.children,
                             {'child2': child2, 'child3': child3}
                             )
        self.assertDictEqual(child2.children, dict())

    def test_set(self):
        comp = Component('name1')
        id_ = id(comp)
        comp.data = 'some thing'
        comp2 = Component('name2')
        comp2.data = 'bar'
        comp.set(comp2)
        self.assertEqual(comp.name, 'name2')
        self.assertEqual(comp.data, 'bar')
        self.assertEqual(id(comp), id_)

    def test_set_data(self):
        comp = Component('name1')
        comp.set_data({'some': 'dict'})
        self.assertDictEqual(comp.data, {'some': 'dict'})

    def test_get_data(self):
        comp = Component('name1')
        comp.data = 8
        obs = comp.get_data()
        self.assertEqual(obs, 8)

    def test_set_get_data_integration(self):
        comp = Component('name1')
        comp.set_data({'a': {'nother': 'dict'}})
        obs = comp.get_data()
        self.assertDictEqual(obs, {'a': {'nother': 'dict'}})

    def test_get_child(self):
        comp = Component('some_name')
        child1 = Component('child1')
        child2 = Component('child2')
        child3 = Component('child3')
        comp.add_child(child1)
        child1.add_child(child2)
        child1.add_child(child3)
        obs = comp.get_child('child1')
        self.assertEqual(obs, child1)
        obs = comp.get_child('child1').get_child('child2')
        self.assertEqual(obs, child2)

    def test_get_child_key_error(self):
        comp = Component('some_name')
        child1 = Component('child1')
        comp.add_child(child1)
        with self.assertRaisesRegex(KeyError, 'child2'):
            comp.get_child('child2')

    def test_gets(self):
        comp = Component('some_name')
        child1 = Component('child1')
        child2 = Component('child2')
        child3 = Component('child3')
        comp.add_child(child1)
        child1.add_child(child2)
        child1.add_child(child3)

        obs = comp.gets('child1', 'child2')
        self.assertEqual(obs, child2)

        obs = comp.gets('child1')
        self.assertEqual(obs, child1)

        obs = comp.gets('child1', 'child3')
        self.assertEqual(obs, child3)

        with self.assertRaisesRegex(KeyError, 'child1'):
            child1.gets('child1', 'child2')

        obs = comp.gets()
        self.assertEqual(obs, comp)

    def test_remove(self):
        child1 = Component('child1')
        child2 = Component('child2')
        child3 = Component('child3')
        child1.add_child(child2)
        child1.add_child(child3)
        child1.remove('child2')
        self.assertDictEqual(child1.children, {'child3': child3})

    def test_set_parent(self):
        comp = Component('name')
        child = Component('child')
        child.set_parent(comp)
        self.assertEqual(child.parent, comp)
        child.remove_parent()
        self.assertIsNone(child.parent)

    def test_str(self):
        child1 = Component('child1')
        child2 = Component('child2')
        child3 = Component('child3')
        child1.add_child(child2)
        child1.add_child(child3)
        child2.set_data({'look': 'here is some data'})
        self.assertIsInstance(str(child1), str)

    def test_from_dict(self):
        demo_dict = {
            'alpha': {
                'components': {
                    'faith_pd': {
                        'construct': 'test',
                        'config': {
                            'file': '/fake/file/path.qza'
                        }
                    },
                }
            },
            'taxonomy': {
                'components': {
                    'agp1': {
                        'components':
                            {
                                'table':
                                    {
                                        'construct': 'test',
                                        'config': {
                                            'file': '/blah.tsv',
                                        }
                                    },
                                'taxonomy':
                                    {
                                        'construct': 'test',
                                        'config': {
                                            'file': '/another.txt',
                                        }

                                    },
                            }
                    },
                    'agp2': {
                        'components':
                            {
                                'table':
                                    {
                                        'construct': 'test',
                                        'config': {
                                            'file': '/blah.tsv',
                                        }
                                    },
                                'taxonomy':
                                    {
                                        'construct': 'test',
                                        'config': {
                                            'file': '/another.txt',
                                        }

                                    },
                            }
                    }
                }
            }
        }

        with patch('microsetta_public_api.resources_alt.constructors') as \
                mock_const:
            MockLoad = Mock()
            MockLoad.return_value.load.return_value = 'loaded data here'
            mock_const.__getitem__.return_value = MockLoad
            obs = Component.from_dict(demo_dict)

        self.assertEqual(obs.gets('alpha', 'faith_pd').data,
                         'loaded data here')

        MockLoad.return_value.load.assert_called_with(file='/another.txt')
        self.assertCountEqual(obs.children, ['alpha', 'taxonomy'])
        self.assertCountEqual(obs.gets('taxonomy').children, ['agp1', 'agp2'])

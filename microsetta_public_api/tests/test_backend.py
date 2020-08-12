from unittest import TestCase

from microsetta_public_api.backend import (
    TrivialLoader,
    constructors,
)


class TestBackend(TestCase):
    def test_trivial_loader(self):
        tl = TrivialLoader()
        kwargs = {'some': 'args', 'are': 'here'}
        obs = tl.load(**kwargs)
        self.assertDictEqual(kwargs, obs)

    def test_constructors_load(self):
        for constructor in constructors.values():
            try:
                self.assertTrue(hasattr(constructor, 'load'))
            except AssertionError:
                raise AssertionError(f"constructor: '{constructor.__name__}' "
                                     f"has not attribute 'load'")

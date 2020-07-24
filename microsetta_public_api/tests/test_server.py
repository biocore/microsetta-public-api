from microsetta_public_api.server import build_app
from microsetta_public_api.utils.testing import TempfileTestCase


class BuildServerTests(TempfileTestCase):

    def test_build_app(self):
        app = build_app()
        self.assertTrue(app)

    def test_build_app_with_json(self):
        test_dict = {'some_resource': 'some_value'}
        app = build_app(resource_updates=test_dict)
        self.assertTrue(app)

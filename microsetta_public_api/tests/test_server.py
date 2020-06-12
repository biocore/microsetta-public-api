import json

from microsetta_public_api.server import build_app
from microsetta_public_api.utils.testing import TempfileTestCase


class BuildServerTests(TempfileTestCase):

    def test_build_app(self):
        app = build_app()
        self.assertTrue(app)

    def test_build_app_with_json(self):
        test_dict = {'some_resource': 'some_value'}
        test_config_file = self.create_tempfile()
        test_config_file.write(json.dumps(test_dict).encode())
        test_config_file.flush()
        app = build_app(resources_config_json=test_config_file.name)
        self.assertTrue(app)

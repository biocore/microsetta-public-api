from microsetta_public_api.server import build_app
from microsetta_public_api.utils.testing import TempfileTestCase


class BuildServerTests(TempfileTestCase):

    def test_build_app(self):
        app = build_app()
        self.assertTrue(app)

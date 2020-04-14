from unittest import TestCase
from unittest import mock

import microsetta_public_api
import microsetta_public_api.server


class FlaskTests(TestCase):

    def setUp(self):

        self.app, self.client = self.build_app_test_client()

    @staticmethod
    def build_app_test_client():
        app = microsetta_public_api.server.build_app()
        client = app.app.test_client()
        return app, client


class AlphaDiversityTests(FlaskTests):

    def test_alpha_diversity_single_sample(self):

        ret_val = {}

        with mock.patch('microsetta_public_api.api.diversity.alpha.get_alpha'
                        '') as mocked_alpha:
            mocked_alpha.return_value = (ret_val, 200)
            _, client = self.build_app_test_client()
            response = client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

        self.assertEqual(response.status_code, 200)

from unittest import TestCase
import json

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

        response = self.client.get(
            '/api/diversity/alpha/observed_otus/sample-foo-bar')

        # will need to be changed when alpha is fully implemented
        exp = {
            'name': None,
            'alpha_metric': 'observed_otus',
            'data': {'sample-foo-bar': 8.25},
        }
        obs = json.loads(response.data)

        self.assertDictEqual(exp, obs)
        self.assertEqual(response.status_code, 200)

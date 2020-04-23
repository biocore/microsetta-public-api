from unittest import TestCase
from unittest.mock import patch
import json
import pandas as pd

import microsetta_public_api
import microsetta_public_api.server
from microsetta_public_api.repo._alpha_repo import AlphaRepo


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
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method,\
                patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_exists.return_value = [True]
            mock_method.return_value = pd.Series({
                'sample-foo-bar': 8.25}, name='observed_otus')

            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

        exp = {
            'sample_id': 'sample-foo-bar',
            'alpha_metric': 'observed_otus',
            'data': 8.25,
        }
        obs = json.loads(response.data)

        self.assertDictEqual(exp, obs)
        self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_unknown_id(self):
        with patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_exists.return_value = [False]

            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

        self.assertRegex(response.data.decode(),
                         "Sample ID not found.")
        self.assertEqual(response.status_code, 404)

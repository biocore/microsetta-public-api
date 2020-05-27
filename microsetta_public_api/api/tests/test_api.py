from unittest.mock import patch
from flask import jsonify
import json
from microsetta_public_api.utils.testing import FlaskTests


class AlphaDiversityTests(FlaskTests):

    def test_alpha_diversity_available_metrics_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.available_metrics_alpha'
                   ) as mock_resources, self.app.app.app_context():
            mock_resources.return_value = jsonify({
                 'alpha_metrics': ['faith_pd', 'chao1']
            }), 200

            _, self.client = self.build_app_test_client()

            exp_metrics = ['faith_pd', 'chao1']
            response = self.client.get(
                '/api/diversity/metrics/alpha/available')

            obs = json.loads(response.data)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual(exp_metrics, obs['alpha_metrics'])
            self.assertEqual(response.status_code, 200)

            mock_resources.return_value = jsonify({
                'alpha_metrics': []
            }), 200
            response = self.client.get(
                '/api/diversity/metrics/alpha/available')

            obs = json.loads(response.data)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual([], obs['alpha_metrics'])
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_available_metrics_api_bad_response(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.available_metrics_alpha'
                   ) as mock_resources, self.app.app.app_context():
            mock_resources.return_value = jsonify({
                'some wrong keyword': ['faith_pd', 'chao1']
            }), 200

            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/api/diversity/metrics/alpha/available')

            self.assertEqual(response.status_code, 500)
            mock_resources.return_value = jsonify({
                'some wrong additional keyword': ['faith_pd', 'chao1'],
                'alpha_metrics': ['faith_pd', 'chao1'],
            }), 200
            self.assertEqual(response.status_code, 500)
            mock_resources.return_value = jsonify({
                'alpha_metrics': 'faith_pd',
            }), 200
            self.assertEqual(response.status_code, 500)

    def test_alpha_diversity_single_sample_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.get_alpha'
                   ) as mock_method, self.app.app.app_context():

            exp = {
                'sample_id': 'sample-foo-bar',
                'alpha_metric': 'observed_otus',
                'data': 8.25,
            }
            mock_output = jsonify(exp), 200
            mock_method.return_value = mock_output

            _, self.client = self.build_app_test_client()
            response = self.client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

            obs = json.loads(response.data)

            self.assertDictEqual(exp, obs)
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_unknown_id_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.get_alpha'
                   ) as mock_method, self.app.app.app_context():

            mock_method.return_value = jsonify(error=404, text="Sample ID "
                                                               "not found."), \
                                       404
            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

        self.assertRegex(response.data.decode(),
                         "Sample ID not found.")
        self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_group_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.alpha_group'
                   ) as mock_method, self.app.app.app_context():
            exp = {
                'alpha_metric': 'observed_otus',
                'alpha_diversity': {'sample-foo-bar': 8.25,
                                    'sample-baz-bat': 9.01,
                                    }
            }
            mock_method.return_value = jsonify(exp), 200

            _, self.client = self.build_app_test_client()

            response = self.client.post(
                '/api/diversity/alpha_group/observed_otus',
                content_type='application/json',
                data=json.dumps({'sample_ids': ['sample-foo-bar',
                                                'sample-baz-bat']
                                 })
            )

            obs = json.loads(response.data)

            self.assertDictEqual(exp, obs)
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_group_unknown_metric_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.alpha_group'
                   ) as mock_method, self.app.app.app_context():

            available_metrics = ['metric1', 'metric2']
            exp = dict(error=404, text=f"Requested metric: 'observed_otus' "
                                       f"is unavailable. Available metrics: "
                                       f"{available_metrics}")
            mock_method.return_value = jsonify(exp), 404

            _, self.client = self.build_app_test_client()

            response = self.client.post(
                '/api/diversity/alpha_group/observed_otus',
                content_type='application/json',
                data=json.dumps({'metric': 'observed_otus',
                                 'sample_ids': ['sample-foo-bar',
                                                'sample-baz-bat']
                                 })
            )
        api_out = json.loads(response.data.decode())
        self.assertEqual(api_out['text'],
                         exp['text'])
        self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_group_unknown_sample_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.alpha_group'
                   ) as mock_method, self.app.app.app_context():
            missing_ids = ['sample-baz-bat']
            exp = dict(missing_ids=missing_ids,
                       error=404, text="Sample ID(s) not found for "
                                       "metric: observed_otus")
            mock_method.return_value = jsonify(exp), 404

            _, self.client = self.build_app_test_client()

            response = self.client.post(
                '/api/diversity/alpha_group/observed_otus',
                content_type='application/json',
                data=json.dumps({'metric': 'observed_otus',
                                 'sample_ids': ['sample-foo-bar',
                                                'sample-baz-bat']
                                 })
            )
            api_out = json.loads(response.data.decode())
            self.assertEqual(api_out, exp)
            self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_group_unknown_sample_api_bad_response(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.alpha_group'
                   ) as mock_method, self.app.app.app_context():
            bad_missing_ids = 'sample-baz-bat'
            exp = dict(missing_ids=bad_missing_ids,
                       error=404, text="Sample ID(s) not found for "
                                       "metric: observed_otus")
            mock_method.return_value = jsonify(exp), 404

            _, self.client = self.build_app_test_client()

            response = self.client.post(
                '/api/diversity/alpha_group/observed_otus',
                content_type='application/json',
                data=json.dumps({'metric': 'observed_otus',
                                 'sample_ids': ['sample-foo-bar',
                                                'sample-baz-bat']
                                 })
            )
            self.assertEqual(response.status_code, 500)

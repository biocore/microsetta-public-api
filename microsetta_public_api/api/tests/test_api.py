from unittest.mock import patch
from flask import jsonify
import json
from microsetta_public_api.utils.testing import FlaskTests


class MetadataCategoryTests(FlaskTests):

    def setUp(self):
        super().setUp()
        self.patcher = patch(
            'microsetta_public_api.api.metadata.category_values')
        self.mock_method = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_metadata_category_values_returns_string_array(self):
        with self.app_context():
            self.mock_method.return_value = jsonify([
                '20s',
                '30s',
                '40s',
                '50',
            ])
        _, self.client = self.build_app_test_client()
        exp = ['20s', '30s', '40s', '50']
        response = self.client.get(
            "/results-api/metadata/category/values/age_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)
        self.mock_method.assert_called_with(category='age_cat')

    def test_metadata_category_values_returns_numeric_array(self):
        with self.app_context():
            self.mock_method.return_value = jsonify([
                20,
                30,
                7.15,
                8.25,
            ])
        _, self.client = self.build_app_test_client()
        exp = [20, 30, 7.15, 8.25]
        response = self.client.get(
            "/results-api/metadata/category/values/age_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)
        self.mock_method.assert_called_with(category='age_cat')

    def test_metadata_category_values_returns_mixed_type_array(self):
        with self.app_context():
            self.mock_method.return_value = jsonify([
                '20s',
                30,
                7.15,
                8.25,
            ])
        _, self.client = self.build_app_test_client()
        exp = ['20s', 30, 7.15, 8.25]
        response = self.client.get(
            "/results-api/metadata/category/values/age_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)
        self.mock_method.assert_called_with(category='age_cat')

    def test_metadata_category_values_returns_empty(self):
        with self.app_context():
            self.mock_method.return_value = jsonify([])
        _, self.client = self.build_app_test_client()
        exp = []
        response = self.client.get(
            "/results-api/metadata/category/values/age_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)
        self.mock_method.assert_called_with(category='age_cat')

    def test_metadata_category_values_returns_404(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(
                error=404, text='Unknown Category',
            ), 404
        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/category/values/age_cat")
        self.assertStatusCode(404, response)
        self.mock_method.assert_called_with(category='age_cat')


class MetadataSampleIdsTests(FlaskTests):

    def setUp(self):
        super().setUp()
        self.patcher = patch(
            'microsetta_public_api.api.metadata.filter_sample_ids')
        self.mock_method = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_metadata_sample_ids_returns_simple(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ]
            })

        _, self.client = self.build_app_test_client()
        exp_ids = ['sample-1', 'sample-2']
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s&bmi_cat=normal")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        self.mock_method.assert_called_with(age_cat='30s', bmi_cat='normal')

    def test_metadata_sample_ids_returns_empty(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                ]
            })

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s&bmi_cat=normal")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertEqual(obs['sample_ids'], [])

    def test_metadata_sample_ids_get_extra_category_in_query_404(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'text': "Metadata category: 'gimme_cat' does not exits.",
                'error': 404
            }), 404

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s&bmi_cat=normal&"
            "gimme_cat=something")
        self.assertStatusCode(404, response)

    def test_metadata_sample_ids_get_age_cat_succeeds(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s")
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        self.mock_method.assert_called_with(age_cat='30s')

    def test_metadata_sample_ids_get_bmi_succeeds(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids?bmi_cat=normal")
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        self.mock_method.assert_called_with(bmi_cat='normal')

    def test_metadata_sample_ids_get_taxonomy_succeeds(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids?taxonomy=ag-genus")
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        self.mock_method.assert_called_with(taxonomy='ag-genus')

    def test_metadata_sample_ids_get_alpha_metric_succeeds(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids?alpha_metric=faith_pd")
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        self.mock_method.assert_called_with(alpha_metric='faith_pd')

    def test_metadata_sample_ids_get_null_parameters_succeeds(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })

        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/sample_ids")
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        self.mock_method.assert_called_with()

    def test_metadata_sample_ids_post_query_builder(self):
        with self.app_context(), patch('microsetta_public_api.api.metadata'
                                       '.filter_sample_ids_query_builder') as \
                mock_method:
            mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })
            _, self.client = self.build_app_test_client()

        request_body = \
            {
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_years",
                        "field": "age_years",
                        "type": "double",
                        "input": "number",
                        "operator": "less",
                        "value": 10.25
                    },
                ],
                "valid": True
            }

        response = self.client.post(
            "/results-api/metadata/sample_ids",
            content_type='application/json',
            data=json.dumps(request_body)
        )
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        mock_method.assert_called_with(body=request_body)

    def test_metadata_sample_ids_post_query_builder_extra_args(self):
        with self.app_context(), patch('microsetta_public_api.api.metadata'
                                       '.filter_sample_ids_query_builder') as \
                mock_method:
            mock_method.return_value = jsonify({
                'sample_ids': [
                    'sample-1',
                    'sample-2',
                ],
            })
            _, self.client = self.build_app_test_client()

        request_body = \
            {
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_years",
                        "field": "age_years",
                        "type": "double",
                        "input": "number",
                        "operator": "less",
                        "value": 10.25
                    },
                ],
                "valid": True
            }

        response = self.client.post(
            "/results-api/metadata/sample_ids?taxonomy=gg&"
            "alpha_metric=faith-pd",
            content_type='application/json',
            data=json.dumps(request_body)
        )
        exp_ids = ['sample-1', 'sample-2']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)
        mock_method.assert_called_with(body=request_body, taxonomy='gg',
                                       alpha_metric='faith-pd')

    def test_metadata_sample_ids_post_query_builder_404(self):
        with self.app_context(), patch('microsetta_public_api.api.metadata'
                                       '.filter_sample_ids_query_builder') as \
                mock_method:
            mock_method.return_value = jsonify(text='Not found', code=404), 404
            _, self.client = self.build_app_test_client()

        request_body = \
            {
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_years",
                        "field": "age_years",
                        "type": "double",
                        "input": "number",
                        "operator": "less",
                        "value": 10.25
                    },
                ],
                "valid": True
            }

        response = self.client.post(
            "/results-api/metadata/sample_ids",
            content_type='application/json',
            data=json.dumps(request_body)
        )
        self.assertStatusCode(404, response)
        mock_method.assert_called_with(body=request_body)


class AlphaDiversityTestCase(FlaskTests):

    def setUp(self):
        super().setUp()
        self.request_content = {
                                'sample_ids': ['sample-foo-bar',
                                               'sample-baz-bat'],
                                }
        self.minimal_response = {'alpha_metric': 'faith_pd',
                                 'alpha_diversity': {'sample1': 5.27},
                                 }


class AlphaDiversityTests(AlphaDiversityTestCase):

    def test_alpha_diversity_available_metrics_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.available_metrics_alpha'
                   ) as mock_resources, self.app_context():
            mock_resources.return_value = jsonify({
                 'alpha_metrics': ['faith_pd', 'chao1']
            }), 200

            _, self.client = self.build_app_test_client()

            exp_metrics = ['faith_pd', 'chao1']
            response = self.client.get(
                '/results-api/diversity/alpha/metrics/available')

            obs = json.loads(response.data)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual(exp_metrics, obs['alpha_metrics'])
            self.assertEqual(response.status_code, 200)

            mock_resources.return_value = jsonify({
                'alpha_metrics': []
            }), 200
            response = self.client.get(
                '/results-api/diversity/alpha/metrics/available')

            obs = json.loads(response.data)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual([], obs['alpha_metrics'])
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_available_metrics_api_bad_response(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.available_metrics_alpha'
                   ) as mock_resources, self.app_context():
            mock_resources.return_value = jsonify({
                'some wrong keyword': ['faith_pd', 'chao1']
            }), 200

            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/results-api/diversity/alpha/metrics/available')

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
                   ) as mock_method, self.app_context():

            exp = {
                'sample_id': 'sample-foo-bar',
                'alpha_metric': 'observed_otus',
                'data': 8.25,
            }
            mock_output = jsonify(exp), 200
            mock_method.return_value = mock_output

            _, self.client = self.build_app_test_client()
            response = self.client.get(
                '/results-api/diversity/alpha/single/observed_otus/'
                'sample-foo-bar')

            obs = json.loads(response.data)

            self.assertDictEqual(exp, obs)
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_unknown_id_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.get_alpha'
                   ) as mock_method, self.app_context():

            mock_method.return_value = jsonify(error=404, text="Sample ID "
                                                               "not found."), \
                                       404
            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/results-api/diversity/alpha/single/observed_otus/'
                'sample-foo-bar')

        self.assertRegex(response.data.decode(),
                         "Sample ID not found.")
        self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_exists_single(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.exists_single'
                   ) as mock_method, self.app_context():

            exp = True
            mock_output = jsonify(exp), 200
            mock_method.return_value = mock_output

            _, self.client = self.build_app_test_client()
            response = self.client.get(
                '/results-api/diversity/alpha/exists/observed_otus?'
                'sample_id=sample-foo-bar')

            obs = json.loads(response.data)

            self.assertEqual(exp, obs)
            self.assertEqual(response.status_code, 200)
            mock_method.assert_called_with(
                alpha_metric='observed_otus',
                sample_id='sample-foo-bar',
            )

    def test_alpha_diversity_exists_single_404(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.exists_single'
                   ) as mock_method, self.app_context():

            mock_method.return_value = jsonify(error=404, text="Metric "
                                                               "not found."), \
                                       404
            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/results-api/diversity/alpha/exists/observed_otus?'
                'sample_id=sample-foo-bar')

        self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_exists_group(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.exists_group'
                   ) as mock_method, self.app_context():

            exp = [True, False, True, True, False]
            mock_output = jsonify(exp), 200
            mock_method.return_value = mock_output

            samples = ['s1', 's2', 's3', 's4', 's5']

            _, self.client = self.build_app_test_client()
            response = self.client.post(
                '/results-api/diversity/alpha/exists/observed_otus?',
                data=json.dumps(samples),
                content_type='application/json',
            )

            obs = json.loads(response.data)

            self.assertEqual(exp, obs)
            self.assertEqual(response.status_code, 200)
            mock_method.assert_called_with(
                alpha_metric='observed_otus',
                body=samples,
            )

    def test_alpha_diversity_exists_group_404(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.exists_single'
                   ) as mock_method, self.app_context():

            mock_method.return_value = jsonify(error=404, text="Metric "
                                                               "not found."), \
                                       404
            _, self.client = self.build_app_test_client()

            response = self.client.post(
                '/results-api/diversity/alpha/exists/observed_otus',
                data=json.dumps(['s1', 's2']),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 404)


class AlphaDiversityGroupTests(AlphaDiversityTestCase):

    def setUp(self):
        super().setUp()
        self.patcher = patch('microsetta_public_api.api.diversity.alpha'
                             '.alpha_group')
        self.mock_method = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_alpha_diversity_group_api(self):
        exp = {
            'alpha_metric': 'observed_otus',
            'alpha_diversity': {'sample-foo-bar': 8.25,
                                'sample-baz-bat': 9.01,
                                }
        }

        with self.app_context():
            self.mock_method.return_value = jsonify(exp), 200

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )

        obs = json.loads(response.data)

        self.assertDictEqual(exp, obs)
        self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_group_unknown_metric_api(self):

        available_metrics = ['metric1', 'metric2']
        exp = dict(error=404, text=f"Requested metric: 'observed_otus' "
                                   f"is unavailable. Available metrics: "
                                   f"{available_metrics}")
        with self.app_context():
            self.mock_method.return_value = jsonify(exp), 404

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        api_out = json.loads(response.data.decode())
        self.assertEqual(api_out['text'],
                         exp['text'])
        self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_group_unknown_sample_api(self):
        missing_ids = ['sample-baz-bat']
        exp = dict(missing_ids=missing_ids,
                   error=404, text="Sample ID(s) not found for "
                                   "metric: observed_otus")

        with self.app_context():
            self.mock_method.return_value = jsonify(exp), 404

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        api_out = json.loads(response.data.decode())
        self.assertEqual(api_out, exp)
        self.assertEqual(response.status_code, 404)

    def test_alpha_diverstiy_group_default_arguments(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(self.minimal_response), 200

        _, self.client = self.build_app_test_client()

        self.client.post(
            '/results-api/diversity/alpha/group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.mock_method.assert_called_with(
            alpha_metric='observed_otus',
            body=self.request_content,
            summary_statistics=True,
            percentiles=None,
            return_raw=False,
        )

    def test_alpha_diversity_group_summary_statistics_queries(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(self.minimal_response), 200

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?summary_statistics=true',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?summary_statistics=true&percentiles=1,2,45',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?summary_statistics=false&percentiles=1,2,45',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?summary_statistics=true&percentiles=0,50,100',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?percentiles=50',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            self.mock_method.return_value = jsonify(
                error=400, text='at least one of summary_statistics'
                                'and return_raw should be true'), 400
        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?summary_statistics=true',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 400)

    def _minimal_query(self):
        minimal_query = '/results-api/diversity/alpha/group/observed_otus'
        return self.client.post(minimal_query,
                                content_type='application/json',
                                data=json.dumps(self.request_content)
                                )

    def test_alpha_diversity_group_summary_statistics_responses(self):
        _, self.client = self.build_app_test_client()
        with self.app_context():
            # test that alpha_metric, alpha_diversity is okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                    'alpha_diversity': {'sample1': 4.5}
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            # test that alpha_metric, group_summary is okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                    'group_summary': {
                        'mean': 4.5,
                        'median': 3.2,
                        'std': 1.2,
                        'group_size': 7,
                        'percentile': [0, 12, 45],
                        'percentile_values': [1.2, 3.0, 3.1],
                    },
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            # test that alpha_metric, group_summary, _and_ alpha_diveristy is
            #  okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                    'group_summary': {
                        'mean': 4.5,
                        'median': 3.2,
                        'std': 1.2,
                        'group_size': 7,
                        'percentile': [0, 12, 45],
                        'percentile_values': [1.2, 3.0, 3.1],
                    },
                    'alpha_diversity': {'sample1': 4.5}
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            # test that only alpha_metric is not okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 500)


class BetaDiversityTests(FlaskTests):

    def test_pcoa_contains(self):
        method = 'microsetta_public_api.api.diversity.beta.pcoa_contains'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = True
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            '/results-api/diversity/beta/unifrac/pcoa/body-site/contains'
            '?sample_id=sample-12'
        )

        self.assertStatusCode(200, response)
        self.assertEqual(json.loads(response.data), True)
        mock_method.assert_called_with(
            beta_metric='unifrac',
            named_sample_set='body-site',
            sample_id='sample-12',
        )

    def test_pcoa_contains_404(self):
        method = 'microsetta_public_api.api.diversity.beta.pcoa_contains'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(text='Sample not found'), 404
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            '/results-api/diversity/beta/unifrac/pcoa/body-site/contains'
            '?sample_id=sample-12'
        )

        self.assertStatusCode(404, response)
        mock_method.assert_called_with(
            beta_metric='unifrac',
            named_sample_set='body-site',
            sample_id='sample-12',
        )


class TaxonomyResourcesAPITests(FlaskTests):

    def setUp(self):
        super().setUp()
        self.patcher = patch('microsetta_public_api.api.taxonomy'
                             '.resources')
        self.mock_method = self.patcher.start()
        self.url = '/results-api/taxonomy/available'
        _, self.client = self.build_app_test_client()

    def tearDown(self):
        self.patcher.stop()

    def test_valid_response_single(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({'resources': [
                'greengenes']}), 200
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)

    def test_valid_response_multiple(self):
        with self.app_context():
            self.mock_method.return_value = jsonify({'resources': [
                'greengenes', 'silva']}), 200
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)

    def test_invalid_response_string(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(
                {'resources': 'greengenes'}), 200
        response = self.client.get(self.url)
        self.assertEqual(500, response.status_code)


class TaxonomyGroupAPITests(FlaskTests):

    def setUp(self):
        super().setUp()
        self.patcher = patch('microsetta_public_api.api.taxonomy'
                             '.summarize_group')
        self.mock_method = self.patcher.start()
        self.request_content = {
            'sample_ids': ['sample-foo-bar',
                           'sample-baz-bat'],
        }

        _, self.client = self.build_app_test_client()

    def tearDown(self):
        self.patcher.stop()

    def test_valid_response(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(
                {
                    'taxonomy': "(((((feature-2)e)d,feature-1)c)b)a;",
                    'features': ['feature-1', 'feature-2'],
                    'feature_values': [5.2, 7.15],
                    'feature_variances': [0, 0],
                }
            ), 200

        response = self.client.post('/results-api/taxonomy/group/greengenes',
                                    content_type='application/json',
                                    data=json.dumps(self.request_content))
        self.assertEqual(200, response.status_code)


class TaxonomySingleSampleAPITests(FlaskTests):

    def setUp(self):
        super().setUp()
        self.patcher = patch('microsetta_public_api.api.taxonomy'
                             '.single_sample')
        self.mock_method = self.patcher.start()
        _, self.client = self.build_app_test_client()

    def tearDown(self):
        self.patcher.stop()

    def test_valid_response_single_sample(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(
                {
                    'taxonomy': "(((((feature-2)e)d,feature-1)c)b)a;",
                    'features': ['feature-1', 'feature-2'],
                    'feature_values': [5.2, 7.15],
                    'feature_variances': [0, 0],
                }
            ), 200

        response = self.client.get(
            '/results-api/taxonomy/single/greengenes/sample-1',
        )
        self.assertEqual(200, response.status_code)


class TaxonomyDataTableTests(FlaskTests):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.valid_response = {'data': [
            {
                "sampleId": "sample1",
                "Kingdom": "Bacteria",
                "Genus": "Bacteroides",
                "relativeAbundance": 0.7,
            },
            {
                "sampleId": "sample1",
                "Kingdom": "Bacteria",
                "Genus": "Clostridium",
                "relativeAbundance": 0.3,
            },
            {
                "sampleId": "sample2",
                "Kingdom": "Bacteria",
                "Genus": "Bacteroides",
                "relativeAbundance": 0.2,
            },
            {
                "sampleId": "sample2",
                "Kingdom": "Bacteria",
                "Genus": None,
                "relativeAbundance": 0.8,
            },
            {
                "sampleId": "sample3",
                "Kingdom": "Bacteria",
                "Genus": "Clostridium",
                "relativeAbundance": 1.0,
            },
        ],
            'columns': [
            {'data': 'sampleId'},
            {'data': 'Kingdom'},
            {'data': 'Genus'},
            {'data': 'relativeAbundance'}
        ]}

    def setUp(self):
        super().setUp()
        self.patcher_single = patch(
            'microsetta_public_api.api.taxonomy.single_sample_taxa_present')
        self.mock_method_single = self.patcher_single.start()
        self.patcher_group = patch(
            'microsetta_public_api.api.taxonomy.group_taxa_present')
        self.mock_method_group = self.patcher_group.start()
        _, self.client = self.build_app_test_client()

    def tearDown(self):
        self.patcher_group.stop()
        self.patcher_single.stop()

    def test_valid_response_single(self):
        with self.app_context():
            self.mock_method_single.return_value = jsonify(
                self.valid_response
            ), 200

        response = self.client.get(
            '/results-api/taxonomy/present/single/greengenes/sample-1',
        )
        self.assertEqual(200, response.status_code)

    def test_valid_response_group(self):
        with self.app_context():
            self.mock_method_group.return_value = jsonify(
                self.valid_response
            ), 200

        response = self.client.post(
            '/results-api/taxonomy/present/group/greengenes',
            content_type='application/json',
            data=json.dumps({'sample_ids': ['sample1', 'sample2']})
        )
        self.assertEqual(200, response.status_code)

    def test_404_valid(self):
        with self.app_context():
            self.mock_method_group.return_value = jsonify(
                error=404, text='sample ids not found!'
            ), 404

        response = self.client.post(
            '/results-api/taxonomy/present/group/greengenes',
            content_type='application/json',
            data=json.dumps({'sample_ids': ['sample1', 'sample2']})
        )
        self.assertEqual(404, response.status_code)


class PlottingTests(FlaskTests):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sample_vega_schema = {
            "data": {"url": "data/population.json"},
            "transform": [{
                "filter": "datum.year == 2000"
            }],
            "mark": "bar",
            "encoding": {
                "x": {
                    "aggregate": "sum",
                    "field": "people",
                    "type": "quantitative",
                    "axis": {"title": "population"}
                }
            },
            "config": {"view": {"step": 15}}
        }

    def test_alpha_percentiles_plot_get(self):
        method = 'microsetta_public_api.api.plotting.plot_alpha_filtered'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                self.sample_vega_schema
            ), 200
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            "/results-api/plotting/diversity/alpha/faith-pd/percentiles-plot"
            "?age_cat=30s&bmi_cat=Normal&percentiles=1,2,3,5"
            "&sample_id=10377.12"
        )
        self.assertStatusCode(200, response)
        self.assertDictEqual(self.sample_vega_schema,
                             json.loads(response.data))
        mock_method.assert_called_with(alpha_metric='faith-pd',
                                       age_cat='30s',
                                       bmi_cat='Normal',
                                       percentiles=[1, 2, 3, 5],
                                       sample_id='10377.12',
                                       )

    def test_alpha_percentiles_plot_get_422(self):
        method = 'microsetta_public_api.api.plotting.plot_alpha_filtered'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                text='Not enough sample IDs'
            ), 422
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            "/results-api/plotting/diversity/alpha/faith-pd/percentiles-plot"
            "?age_cat=30s&bmi_cat=Normal&percentiles=1,2,3,5"
            "&sample_id=10377.12"
        )
        self.assertStatusCode(422, response)

    def test_alpha_percentiles_plot_get_404(self):
        method = 'microsetta_public_api.api.plotting.plot_alpha_filtered'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                text='not found', code=404,
            ), 404
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            "/results-api/plotting/diversity/alpha/faith-pd/percentiles-plot"
            "?age_cat=30s&bmi_cat=Normal&percentiles=1,2,3,5"
            "&sample_id=10377.12"
        )
        self.assertStatusCode(404, response)

    def test_alpha_percentiles_plot_post(self):
        method = 'microsetta_public_api.api.plotting' \
                 '.plot_alpha_filtered_json_query'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                self.sample_vega_schema
            ), 200
            _, self.client = self.build_app_test_client()

        request_body = \
            {
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_years",
                        "field": "age_years",
                        "type": "double",
                        "input": "number",
                        "operator": "less",
                        "value": 10.25
                    },
                ],
                "valid": True
            }

        response = self.client.post(
            "/results-api/plotting/diversity/alpha/faith-pd/percentiles-plot"
            "?&percentiles=1,2,3,5&sample_id=10377.12",
            content_type='application/json',
            data=json.dumps(request_body)
        )
        self.assertStatusCode(200, response)
        self.assertDictEqual(self.sample_vega_schema,
                             json.loads(response.data))
        mock_method.assert_called_with(alpha_metric='faith-pd',
                                       body=request_body,
                                       percentiles=[1, 2, 3, 5],
                                       sample_id='10377.12',
                                       )

    def test_alpha_percentiles_plot_post_404(self):
        method = 'microsetta_public_api.api.plotting' \
                 '.plot_alpha_filtered_json_query'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                text='not found', code=404
            ), 404
            _, self.client = self.build_app_test_client()

        request_body = \
            {
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_years",
                        "field": "age_years",
                        "type": "double",
                        "input": "number",
                        "operator": "less",
                        "value": 10.25
                    },
                ],
                "valid": True
            }

        response = self.client.post(
            "/results-api/plotting/diversity/alpha/faith-pd/percentiles-plot"
            "?&percentiles=1,2,3,5&sample_id=10377.12",
            content_type='application/json',
            data=json.dumps(request_body)
        )
        self.assertStatusCode(404, response)
        mock_method.assert_called_with(alpha_metric='faith-pd',
                                       body=request_body,
                                       percentiles=[1, 2, 3, 5],
                                       sample_id='10377.12',
                                       )

    def test_beta_vega_plot(self):
        method = 'microsetta_public_api.api.plotting.plot_beta'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                self.sample_vega_schema
            )
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            "/results-api/plotting/diversity/beta/unifrac/pcoa/body-site/vega"
            "?sample_id=10377.12",
        )
        self.assertStatusCode(200, response)
        self.assertDictEqual(self.sample_vega_schema,
                             json.loads(response.data))
        mock_method.assert_called_with(
            beta_metric='unifrac',
            named_sample_set='body-site',
            sample_id='10377.12',
        )

    def test_beta_vega_plot_404(self):
        method = 'microsetta_public_api.api.plotting.plot_beta'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                text='Not found',
                code=404
            ), 404
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            "/results-api/plotting/diversity/beta/unifrac/pcoa/body-site/vega"
            "?sample_id=10377.12",
        )
        self.assertStatusCode(404, response)
        mock_method.assert_called_with(
            beta_metric='unifrac',
            named_sample_set='body-site',
            sample_id='10377.12',
        )


class EmperorTests(FlaskTests):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sample_emperor_schema = {
            "decomposition": {
                "coordinates": [
                    [-0.1776, 0.6011, -0.2033, -0.3368],
                    [0.2561, 0.4013, -0.32037, 0.09316],
                ],
                "percents_explained":
                    [63.21, 23.25, 8.55, 3.14],
                "sample_ids":
                    ['sample-1', 'sample-715'],
            },
            "metadata": [
                ["fecal", 0.7, 9, "30s", "Normal"],
                ["sebum", 20.4, None, "40s", "Overweight"]
            ],
            "metadata_headers": [
                "body-habitat",
                "latitude",
                "days_post_surgery",
                "age_cat",
                "bmi_cat",
            ],
        }

    def test_emperor_plot(self):
        method = 'microsetta_public_api.api.emperor.plot_pcoa'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                self.sample_emperor_schema
            )
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            '/results-api/plotting/diversity/beta/unifrac/pcoa/body-habitat/'
            'emperor'
        )

        self.assertStatusCode(200, response)
        self.assertDictEqual(self.sample_emperor_schema,
                             json.loads(response.data))
        mock_method.assert_called_with(
            beta_metric='unifrac',
            named_sample_set='body-habitat',
        )

    def test_emperor_plot_404(self):
        method = 'microsetta_public_api.api.emperor.plot_pcoa'
        with self.app_context(), patch(method) as mock_method:
            mock_method.return_value = jsonify(
                text='Not found', code=404
            ), 404
            _, self.client = self.build_app_test_client()

        response = self.client.get(
            '/results-api/plotting/diversity/beta/unifrac/pcoa/body-habitat/'
            'emperor'
        )

        self.assertStatusCode(404, response)
        mock_method.assert_called_with(
            beta_metric='unifrac',
            named_sample_set='body-habitat',
        )

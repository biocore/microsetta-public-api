import pandas as pd
import altair as alt
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.api.metadata import _format_query, \
    _validate_query, _filter_matching_ids
from microsetta_public_api.utils._utils import jsonify


def plot_alpha_filtered(alpha_metric=None, percentiles=None,
                        sample_id=None, **kwargs):
    repo = MetadataRepo()
    query = _format_query(kwargs)
    is_invalid = _validate_query(kwargs, repo)
    if is_invalid:
        return is_invalid

    return _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles,
                                                query, repo, sample_id)


def plot_alpha_filtered_json_query(body, alpha_metric=None, percentiles=None,
                                   sample_id=None):
    repo = MetadataRepo()

    return _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles,
                                                body, repo, sample_id)


def _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles, query,
                                         repo, sample_id):
    error_code, error_response, matching_ids = _filter_ids(repo, alpha_metric,
                                                           query, sample_id)

    # TODO ideally these would raise an exception lower in the stack and
    #  then be handled by an exception handler, but for now they are clunky
    #  to refactor due to execution flow interruption
    if error_response:
        return error_response, error_code
    if len(matching_ids) <= 1:
        return jsonify(text='Did not find more than 1 ID\'s matching '
                            'request. Plot would be nonsensical.'), 422

    alpha_summary, sample_diversity = _get_alpha_info(alpha_metric,
                                                      matching_ids,
                                                      percentiles, sample_id)

    chart = _plot_percentiles_plot(alpha_metric, alpha_summary,
                                   sample_diversity)

    return jsonify(**chart.to_dict()), 200


def _plot_percentiles_plot(metric, summary, sample_value=None):
    df = pd.DataFrame({'percentile': summary['percentile'],
                       'values': summary['percentile_values'],
                       }
                      )
    chart = alt.Chart(df).encode(
        x=alt.X("values", stack=None, title=metric),
        y=alt.Y("percentile", title='Percentile'),
    )
    chart = chart.mark_area(opacity=0.3) + chart.mark_line() + \
        chart.mark_point()
    if sample_value:
        # get_alpha_diversity returns a pd.Series, so subset it
        sample_df = pd.DataFrame({'sample-value': [sample_value]})
        vertical_line = alt.Chart(sample_df).mark_rule().encode(
            x=alt.X('sample-value'),
        )
        chart = (chart + vertical_line)
    return chart


def _get_alpha_info(alpha_metric, matching_ids, percentiles, sample_id):
    alpha_repo = AlphaRepo()
    # retrieve the alpha diversity for each sample
    alpha_series = alpha_repo.get_alpha_diversity(matching_ids,
                                                  alpha_metric,
                                                  )
    alpha_ = Alpha(alpha_series, percentiles=percentiles)
    alpha_summary = alpha_.get_group(name='').to_dict()
    if sample_id:
        sample_diversity, = alpha_repo.get_alpha_diversity(sample_id,
                                                           alpha_metric)
    else:
        sample_diversity = None
    return alpha_summary, sample_diversity


def _filter_ids(repo, alpha_metric, query, sample_id):
    matching_ids = repo.sample_id_matches(query)
    matching_ids, error_code, error_response = _filter_matching_ids(
        matching_ids, AlphaRepo, 'available_metrics', alpha_metric, 'metric',
    )
    if sample_id:
        alpha_repo = AlphaRepo()
        if not all(alpha_repo.exists([sample_id], alpha_metric)):
            return 404, jsonify(error=404, text="Sample ID not found."), \
                   []
        _, error_code, error_response = _filter_matching_ids(
            [sample_id], AlphaRepo, 'available_metrics', alpha_metric,
            'metric', error_code=error_code, error_response=error_response,
        )
    return error_code, error_response, matching_ids


def plot_beta(beta_metric, named_sample_set, sample_id=None):
    raise NotImplementedError()

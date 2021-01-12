import pandas as pd
import altair as alt
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.api.metadata import _format_query, \
    _validate_query, _get_repo_alt as _get_metadata_repo
from microsetta_public_api.api.diversity.alpha import _validate_dataset_alpha
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.utils._utils import jsonify
from microsetta_public_api.exceptions import UnknownID


def _alpha_repo_getter():
    return AlphaRepo()


def _metadata_repo_getter():
    return MetadataRepo()


def _alpha_repo_getter_alt(dataset):
    def _getter():
        alpha_resource = _validate_dataset_alpha(dataset, get_resources)
        return AlphaRepo(alpha_resource.data)
    return _getter


def plot_alpha_filtered_alt(dataset, alpha_metric=None, percentiles=None,
                            sample_id=None, **kwargs):

    repo = _get_metadata_repo(dataset, get_resources)
    query = _format_query(kwargs)
    is_invalid = _validate_query(kwargs, repo)
    if is_invalid:
        return is_invalid

    alpha_repo_getter = _alpha_repo_getter_alt(dataset)
    return _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles,
                                                query, repo, sample_id,
                                                alpha_repo_getter,
                                                )


def plot_alpha_filtered(alpha_metric=None, percentiles=None,
                        sample_id=None, **kwargs):
    repo = _metadata_repo_getter()
    query = _format_query(kwargs)
    is_invalid = _validate_query(kwargs, repo)
    if is_invalid:
        return is_invalid

    return _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles,
                                                query, repo, sample_id,
                                                _alpha_repo_getter,
                                                )


def plot_alpha_filtered_json_query_alt(dataset, body, alpha_metric=None,
                                       percentiles=None,
                                       sample_id=None):
    repo = _get_metadata_repo(dataset, get_resources)
    alpha_repo_getter = _alpha_repo_getter_alt(dataset)
    return _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles,
                                                body, repo, sample_id,
                                                alpha_repo_getter,
                                                )


def plot_alpha_filtered_json_query(body, alpha_metric=None, percentiles=None,
                                   sample_id=None):
    repo = _metadata_repo_getter()

    return _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles,
                                                body, repo, sample_id,
                                                _alpha_repo_getter,
                                                )


def _plot_alpha_percentiles_querybuilder(alpha_metric, percentiles, query,
                                         repo, sample_id, alpha_repo_getter):
    matching_ids = _filter_ids(repo, alpha_repo_getter(), alpha_metric, query,
                               sample_id)

    if len(matching_ids) <= 1:
        return jsonify(text='Did not find more than 1 ID\'s matching '
                            'request. Plot would be nonsensical.'), 422

    alpha_summary, sample_diversity = _get_alpha_info(alpha_metric,
                                                      matching_ids,
                                                      percentiles,
                                                      sample_id,
                                                      alpha_repo_getter,
                                                      )

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


def _get_alpha_info(alpha_metric, matching_ids, percentiles, sample_id,
                    alpha_repo_getter
                    ):
    alpha_repo = alpha_repo_getter()
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


def _filter_ids(metadata_repo, alpha_repo, alpha_metric, query, sample_id):
    matching_ids = metadata_repo.sample_id_matches(query)
    matches_alpha = alpha_repo.exists(matching_ids, alpha_metric)
    matching_ids = [id_ for id_, exists_ in zip(matching_ids, matches_alpha)
                    if exists_]
    if sample_id:
        if not all(alpha_repo.exists([sample_id], alpha_metric)):
            raise UnknownID(sample_id)
    return matching_ids


def plot_beta_alt(beta_metric, named_sample_set, sample_id=None):
    raise NotImplementedError()


def plot_beta(beta_metric, named_sample_set, sample_id=None):
    raise NotImplementedError()

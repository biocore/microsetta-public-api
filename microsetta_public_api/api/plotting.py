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

    matching_ids = repo.sample_id_matches(query)

    matching_ids, error_code, error_response = _filter_matching_ids(
        matching_ids, AlphaRepo, 'available_metrics', alpha_metric, 'metric',
    )
    if sample_id:
        _, error_code, error_response = _filter_matching_ids(
            [sample_id], AlphaRepo, 'available_metrics', alpha_metric,
            'metric', error_code=error_code, error_response=error_response,
        )

    if error_response:
        return error_response, error_code

    alpha_repo = AlphaRepo()

    # retrieve the alpha diversity for each sample
    alpha_series = alpha_repo.get_alpha_diversity(matching_ids,
                                                  alpha_metric,
                                                  )
    alpha_ = Alpha(alpha_series, percentiles=percentiles)
    alpha_summary = alpha_.get_group(name='').to_dict()

    df = pd.DataFrame({'percentile': alpha_summary['percentile'],
                       'values': alpha_summary['percentile_values'],
                       }
                      )
    chart = alt.Chart(df).encode(
        x=alt.X("values", stack=None, title=alpha_metric),
        y=alt.Y("percentile", title='Percentile'),
    )

    chart = chart.mark_area(opacity=0.3) + chart.mark_line() + \
        chart.mark_point()

    if sample_id:
        # get_alpha_diversity returns a pd.Series, so subset it
        sample_diversity, = alpha_repo.get_alpha_diversity(sample_id,
                                                           alpha_metric)
        sample_df = pd.DataFrame({'sample-value': [sample_diversity]})
        vertical_line = alt.Chart(sample_df).mark_rule().encode(
            x=alt.X('sample-value'),
            )
        chart = (chart + vertical_line)

    return jsonify(**chart.to_dict()), 200


if __name__ == "__main__":
    plot_alpha_filtered()

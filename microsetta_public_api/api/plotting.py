import pandas as pd
import altair as alt
from flask import send_file
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.api.metadata import _format_query, \
    _validate_query, _get_repo_alt as _get_metadata_repo
from microsetta_public_api.api.diversity.alpha import _validate_dataset_alpha
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.utils._utils import jsonify
from microsetta_public_api.exceptions import UnknownID
from microsetta_public_api.utils._utils import stepwise_resource_getter
from microsetta_public_api.config import schema
from microsetta_public_api.repo._pcoa_repo import PCoARepo
from microsetta_public_api.exceptions import UnknownResource
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib as mpl
mpl.rcParams['agg.path.chunksize'] = 10000


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


def _get_pcoa_repo(dataset):
    pcoas = stepwise_resource_getter(
        get_resources(),
        dataset,
        schema.pcoa_kw,
        'pcoa',
    )
    pcoa_repo = PCoARepo(pcoas.data)
    return pcoa_repo


def _plot_ids(ax, x, y, size, marker='.', color=None, **kwargs):
    """Plot points, return the used color"""
    # plot is faster than scatter, go figure...
    return ax.plot(x, y, color=color, markersize=size, marker=marker,
                   linestyle='None', **kwargs)[0].get_color()


def _make_mpl_fig(series, x, y, target):
    """given metadata, coordinates and a target, make a figure"""
    # get all the bits organized
    df = pd.DataFrame([], index=series.index)
    df['col'] = series
    df['x'] = x
    df['y'] = y

    # ax1 -> plot
    # ax2 -> legend
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]},
                                   figsize=(5, 3))

    # clean up the plots
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax2.axis('off')

    # determine the point size based on the total number of samples to plot
    n = len(series)
    if n < 5000:
        background_size = 5
    elif n < 50000:
        background_size = 1
    else:
        background_size = 0.5

    # plot each group, keep the name and color for the legend
    names = []
    colors = []
    for name, grp in df.groupby('col'):
        colors.append(_plot_ids(ax1, grp['x'], grp['y'], background_size))
        names.append(name)

    # plot and emphasize our target
    target = df.loc[target]
    colors.append(_plot_ids(ax1, target['x'], target['y'], 30, marker='*',
                            markeredgecolor='black', markeredgewidth=1.5))
    names.append('You')

    # construct a legend
    patches = [mpatches.Patch(color=c, label=n) for c, n in zip(colors, names)]
    ax2.legend(handles=patches, fontsize=10, loc='upper center')

    # make it clean
    fig.tight_layout()

    # serialize the figure
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    output.seek(0)

    # clean up to make matplotlib happy
    plt.close(fig)

    return output


def plot_beta_alt_mpl(dataset, beta_metric, named_sample_set, sample_id=None,
                      category=None):
    pcoa_repo = _get_pcoa_repo(dataset)
    metadata_repo = _get_metadata_repo(dataset, get_resources)

    if not pcoa_repo.has_pcoa(named_sample_set, beta_metric):
        raise UnknownResource(f"No PCoA for named_sample_set="
                              f"'{named_sample_set}',beta_metric="
                              f"'{beta_metric}'"
                              )
    # check metadata repo for the requested categories
    has_category = metadata_repo.has_category([category])
    missing_categories = [cat for i, cat in enumerate([category, ])
                          if not has_category[i]]
    if len(missing_categories) > 0:
        raise UnknownResource(f"Missing specified metadata categories: "
                              f"{missing_categories}"
                              )
    pcoa = pcoa_repo.get_pcoa(named_sample_set, beta_metric)
    metadata = metadata_repo.get_metadata(category)

    x = pcoa.samples[0]
    y = pcoa.samples[1]
    response = _make_mpl_fig(metadata, x, y, sample_id)

    return send_file(response, mimetype='image/png', as_attachment=True,
                     attachment_filename='pcoa.png', conditional=True)

from microsetta_public_api.utils import jsonify
from microsetta_public_api.utils._utils import stepwise_resource_getter
from microsetta_public_api.repo._pcoa_repo import PCoARepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.config import schema
from microsetta_public_api.api.metadata import _get_repo as _get_metadata_repo
from microsetta_public_api.exceptions import UnknownResource


def _get_pcoa_repo(dataset):
    pcoas = stepwise_resource_getter(
        get_resources(),
        dataset,
        schema.pcoa_kw,
        'pcoa',
    )
    taxonomy_repo = PCoARepo(pcoas.data)
    return taxonomy_repo


def plot_pcoa_alt(dataset, beta_metric, named_sample_set, metadata_categories,
                  fillna='nan'):
    pcoa_repo = _get_pcoa_repo(dataset)
    metadata_repo = _get_metadata_repo(get_resources)

    return _plot_pcoa(beta_metric, fillna, metadata_categories,
                      named_sample_set, metadata_repo, pcoa_repo)


def plot_pcoa(beta_metric, named_sample_set, metadata_categories,
              fillna='nan'):
    pcoa_repo = PCoARepo()
    metadata_repo = MetadataRepo()

    return _plot_pcoa(beta_metric, fillna, metadata_categories,
                      named_sample_set, metadata_repo, pcoa_repo)


def _plot_pcoa(beta_metric, fillna, metadata_categories, named_sample_set,
               metadata_repo, pcoa_repo):
    if not pcoa_repo.has_pcoa(named_sample_set, beta_metric):
        raise UnknownResource(f"No PCoA for named_sample_set="
                              f"'{named_sample_set}',beta_metric="
                              f"'{beta_metric}'"
                              )
    # check metadata repo for the requested categories
    has_category = metadata_repo.has_category(metadata_categories)
    missing_categories = [cat for i, cat in enumerate(metadata_categories)
                          if not has_category[i]]
    if len(missing_categories) > 0:
        raise UnknownResource(f"Missing specified metadata categories: "
                              f"{missing_categories}"
                              )
    pcoa = pcoa_repo.get_pcoa(named_sample_set, beta_metric)
    # grab the sample ids from the PCoA
    samples = pcoa.samples.index
    # metadata for samples not in the repo will be filled in as None
    metadata = metadata_repo.get_metadata(metadata_categories,
                                          sample_ids=samples,
                                          fillna=fillna,
                                          )
    response = dict()
    response['decomposition'] = {
        "coordinates": pcoa.samples.values.tolist(),
        "percents_explained": list(100 * prop for
                                   prop in pcoa.proportion_explained),
        "sample_ids": list(samples),
    }
    response["metadata"] = metadata.values.tolist()
    response["metadata_headers"] = metadata.columns.tolist()
    return jsonify(response), 200

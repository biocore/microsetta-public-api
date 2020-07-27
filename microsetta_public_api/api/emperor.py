from microsetta_public_api.utils import jsonify
from microsetta_public_api.repo._pcoa_repo import PCoARepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo


def plot_pcoa(beta_metric, named_sample_set, metadata_categories):
    pcoa_repo = PCoARepo()
    metadata_repo = MetadataRepo()

    if not pcoa_repo.has_pcoa(named_sample_set, beta_metric):
        return jsonify(
                text=f"No PCoA for named_sample_set='{named_sample_set}',"
                     f"beta_metric='{beta_metric}'",
                code=404
            ), 404

    # check metadata repo for the requested categories
    has_category = metadata_repo.has_category(metadata_categories)
    missing_categories = [cat for i, cat in enumerate(metadata_categories)
                          if not has_category[i]]
    if len(missing_categories) > 0:
        return jsonify(text="Missing specified metadata categories.",
                       missing_categories=missing_categories,
                       ), 404

    pcoa = pcoa_repo.get_pcoa(named_sample_set, beta_metric)
    # grab the sample ids from the PCoA
    samples = pcoa.samples.index

    # metadata for samples not in the repo will be filled in as None
    metadata = metadata_repo.get_metadata(metadata_categories,
                                          sample_ids=samples)

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

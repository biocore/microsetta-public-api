from microsetta_public_api.utils._utils import jsonify
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.config import schema
from microsetta_public_api.api.metadata import _get_repo_alt as \
    _get_metadata_repo


def available():
    resources = get_resources()
    escape = {schema.metadata_kw}
    dataset_key = 'datasets'
    detail_key = '__dataset_detail__'

    if dataset_key not in resources:
        return jsonify({}), 200

    datasets = {}
    for k, v in resources[dataset_key].items():
        if k in escape:
            continue
        datasets[k] = v.get(detail_key)

    return jsonify(datasets), 200


def datasets_for_sample(sample_id):
    resources = get_resources()
    datasets_with_sample_id = []
    datasets = list(resources['datasets'].keys())
    # remove this so the __metadata__ key, which is not a dataset, is not
    # checked for sample ID membership
    if '__metadata__' in datasets:
        datasets.remove('__metadata__')
    for dataset in datasets:
        if dataset_sample_exists(dataset, sample_id):
            datasets_with_sample_id.append(dataset)

    return datasets_with_sample_id


def dataset_sample_exists(dataset, sample_id):
    metadata = _get_metadata_repo(dataset)
    return metadata.has_sample_id(sample_id)


def dataset_detail(dataset):
    resources = get_resources()
    dataset_key = 'datasets'
    detail_key = '__dataset_detail__'

    if dataset_key not in resources:
        return jsonify({}), 404

    detail = resources[dataset_key].get(dataset)
    if detail is None:
        return jsonify({'message': f"{dataset} not found"}), 404

    return jsonify({dataset: detail[detail_key]}), 200


# def dataset_contains(dataset, sample_id):
#     pass

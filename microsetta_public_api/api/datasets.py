from microsetta_public_api.utils._utils import jsonify
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.config import schema


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

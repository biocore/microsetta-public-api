from microsetta_public_api.utils._utils import jsonify
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.config import schema


def available():
    resources = get_resources()
    escape = {schema.metadata_kw}
    dataset_key = 'datasets'

    if dataset_key not in resources:
        return jsonify([]), 200

    datasets = list(filter(
        lambda x: x not in escape,
        resources[dataset_key].keys()
    ))
    return jsonify(datasets), 200


def dataset_detail(dataset):
    pass


def dataset_contains(dataset, sample_id):
    pass

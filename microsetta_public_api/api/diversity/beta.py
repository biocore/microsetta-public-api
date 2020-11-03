from microsetta_public_api.utils import jsonify
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.repo._beta_repo import BetaRepo
from microsetta_public_api.exceptions import (
    UnknownResource,
)
from microsetta_public_api.config import schema


def _validate_dataset_beta(dataset, resource_getter):
    getter = resource_getter()
    dataset_info = ('datasets', dataset)
    if not getter.has(*dataset_info):
        raise UnknownResource(f"Unknown dataset: '{dataset}'")
    dataset_resource = getter.gets(*dataset_info)

    beta_kw = schema.beta_kw
    if not dataset_resource.has(beta_kw):
        raise UnknownResource(f"No beta data (kw: '{beta_kw}') for "
                              f"dataset='{dataset}'.")
    beta_resource = dataset_resource.gets(beta_kw)
    return beta_resource


def pcoa_contains_alt(named_sample_set, sample_id):
    raise NotImplementedError()


def pcoa_contains(named_sample_set, sample_id):
    raise NotImplementedError()


def k_nearest(dataset, beta_metric, k, sample_id):
    beta_resource = _validate_dataset_beta(dataset,
                                           resource_getter=get_resources)
    beta_repo = BetaRepo(beta_resource.data)
    k_nearest_ids = beta_repo.k_nearest(sample_id=sample_id,
                                        metric=beta_metric,
                                        k=k,
                                        )
    return jsonify(k_nearest_ids), 200

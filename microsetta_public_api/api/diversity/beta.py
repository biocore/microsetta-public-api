from microsetta_public_api.utils import jsonify
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.repo._beta_repo import NeighborsRepo
from microsetta_public_api.exceptions import (
    UnknownResource,
)
from microsetta_public_api.config import schema


def _validate_dataset_neighbors(dataset, resource_getter):
    try:
        dataset_resource = resource_getter().gets('datasets', dataset)
    except KeyError:
        raise UnknownResource(f"Unknown dataset: '{dataset}'")

    if not dataset_resource.has(schema.neighbors_kw):
        raise UnknownResource(f"No neighbors data (kw: "
                              f"'{schema.neighbors_kw}') "
                              f"for dataset='{dataset}'.")
    return dataset_resource.gets(schema.neighbors_kw)


def pcoa_contains_alt(named_sample_set, sample_id):
    raise NotImplementedError()


def pcoa_contains(named_sample_set, sample_id):
    raise NotImplementedError()


def k_nearest(dataset, beta_metric, k, sample_id):
    beta_resource = _validate_dataset_neighbors(dataset,
                                                resource_getter=get_resources)
    neigh_repo = NeighborsRepo(beta_resource.data)
    k_nearest_ids = neigh_repo.k_nearest(sample_id=sample_id,
                                         metric=beta_metric,
                                         k=k,
                                         )
    return jsonify(k_nearest_ids), 200

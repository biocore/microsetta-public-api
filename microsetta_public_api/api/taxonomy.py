from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo
from microsetta_public_api.utils import jsonify
from microsetta_public_api.models._taxonomy import Taxonomy
from microsetta_public_api.utils._utils import (validate_resource,
                                                check_missing_ids,
                                                )


def single_sample(sample_id, resource):
    sample_ids = [sample_id]
    return _summarize_group(sample_ids, resource)


def summarize_group(body, resource):
    sample_ids = body['sample_ids']
    return _summarize_group(sample_ids, resource)


def _summarize_group(sample_ids, table_name):
    taxonomy_repo = TaxonomyRepo()
    available_resources = taxonomy_repo.resources()

    type_ = 'resource'
    missing_resource = validate_resource(available_resources, table_name,
                                         type_)
    if missing_resource:
        return missing_resource

    missing_ids = [id_ for id_ in sample_ids if
                   not taxonomy_repo.exists(id_, table_name)]

    missing_ids_msg = check_missing_ids(missing_ids, table_name, type_)
    if missing_ids_msg:
        return missing_ids_msg

    table = taxonomy_repo.table(table_name)
    features = taxonomy_repo.feature_data_taxonomy(table_name)
    variances = taxonomy_repo.variances(table_name)

    taxonomy_ = Taxonomy(table, features, variances)
    taxonomy_data = taxonomy_.get_group(sample_ids, '').to_dict()
    del taxonomy_data['name']
    del taxonomy_data['feature_ranks']
    response = jsonify(taxonomy_data)
    return response, 200


def resources():
    taxonomy_repo = TaxonomyRepo()
    ret_val = {
        'resources': taxonomy_repo.resources(),
    }
    return jsonify(ret_val), 200

from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo
from microsetta_public_api.utils import jsonify
from microsetta_public_api.utils._utils import (validate_resource,
                                                check_missing_ids,
                                                )


def single_sample(sample_id, resource):
    sample_ids = [sample_id]
    return _summarize_group(sample_ids, resource)


def summarize_group(body, resource):
    sample_ids = body['sample_ids']
    return _summarize_group(sample_ids, resource)


def _check_resource_and_missing_ids(taxonomy_repo, sample_ids, resource):
    available_resources = taxonomy_repo.resources()

    type_ = 'resource'
    missing_resource = validate_resource(available_resources, resource,
                                         type_)
    if missing_resource:
        return missing_resource

    missing_ids = [id_ for id_ in sample_ids if
                   not taxonomy_repo.exists(id_, resource)]

    missing_ids_msg = check_missing_ids(missing_ids, resource, type_)
    if missing_ids_msg:
        return missing_ids_msg


def _summarize_group(sample_ids, table_name):
    taxonomy_repo = TaxonomyRepo()
    error_response = _check_resource_and_missing_ids(taxonomy_repo,
                                                     sample_ids, table_name)
    if error_response:
        return error_response
    taxonomy_ = taxonomy_repo.model(table_name)

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


def single_sample_taxa_present(sample_id, resource):
    sample_ids = [sample_id]
    return _present_microbes_taxonomy_table(sample_ids, resource)


def group_taxa_present(body, resource):
    sample_ids = body['sample_ids']
    return _present_microbes_taxonomy_table(sample_ids, resource)


def _present_microbes_taxonomy_table(sample_ids, resource):
    taxonomy_repo = TaxonomyRepo()
    error_response = _check_resource_and_missing_ids(taxonomy_repo,
                                                     sample_ids, resource)
    if error_response:
        return error_response

    taxonomy_ = taxonomy_repo.model(resource)
    taxonomy_table = taxonomy_.presence_data_table(sample_ids)
    response = jsonify(taxonomy_table.to_dict())
    return response, 200

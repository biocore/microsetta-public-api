from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo
from microsetta_public_api.utils import jsonify
from microsetta_public_api.config import schema
from microsetta_public_api.resources_alt import get_resources
from microsetta_public_api.utils._utils import (
    validate_resource,
    check_missing_ids,
    stepwise_resource_getter,
    validate_resource_alt,
    check_missing_ids_alt
)
from empress import Empress


def _get_taxonomy_repo(dataset):
    tables = stepwise_resource_getter(
        get_resources(),
        dataset,
        schema.taxonomy_kw,
        'taxonomy',
    )
    taxonomy_repo = TaxonomyRepo(tables.data)
    return taxonomy_repo


def single_sample_alt(dataset, sample_id, resource):
    sample_ids = [sample_id]
    taxonomy_repo = _get_taxonomy_repo(dataset)
    return _summarize_group(sample_ids, resource, taxonomy_repo)


def single_sample(sample_id, resource):
    sample_ids = [sample_id]
    taxonomy_repo = TaxonomyRepo()
    return _summarize_group(sample_ids, resource, taxonomy_repo)


def summarize_group_alt(body, dataset, resource):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    sample_ids = body['sample_ids']
    return _summarize_group(sample_ids, resource, taxonomy_repo)


def summarize_group(body, resource):
    sample_ids = body['sample_ids']
    taxonomy_repo = TaxonomyRepo()
    return _summarize_group(sample_ids, resource, taxonomy_repo)


def _check_resource_and_missing_ids_alt(taxonomy_repo, sample_ids, resource):
    available_resources = taxonomy_repo.resources()
    type_ = 'resource'
    validate_resource_alt(available_resources, resource, type_)
    missing_ids = [id_ for id_ in sample_ids if
                   not taxonomy_repo.exists(id_, resource)]
    check_missing_ids_alt(missing_ids, resource, type_)


def _taxonomy_counts(resource, taxonomy_repo, level, sample_ids):
    if sample_ids == []:
        sample_ids = None

    taxonomy_ = taxonomy_repo.model(resource)

    counts = taxonomy_.get_counts(level, sample_ids)
    response = jsonify(counts)
    return response


def group_counts(body, dataset, resource, level):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    sample_ids = body['sample_ids']
    _check_resource_and_missing_ids_alt(taxonomy_repo, sample_ids, resource)
    response = _taxonomy_counts(resource, taxonomy_repo, level, sample_ids)
    return response, 200


def single_counts(dataset, resource, sample_id, level):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    sample_ids = [sample_id]
    _check_resource_and_missing_ids_alt(taxonomy_repo, sample_ids, resource)
    response = _taxonomy_counts(resource, taxonomy_repo, level, sample_ids)
    return response, 200


def get_empress(dataset, resource, sample_id=None):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    taxonomy_model = taxonomy_repo.model(resource)
    bp_tree = taxonomy_model.bp_tree
    feature_metadata = taxonomy_model.get_collapsed_table_data(sample_id)
    empress_model = Empress(bp_tree, feature_metadata=feature_metadata)
    return empress_model.to_dict()


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


def _summarize_group(sample_ids, table_name, taxonomy_repo):

    error_response = _check_resource_and_missing_ids(taxonomy_repo,
                                                     sample_ids, table_name)
    if error_response:
        return error_response
    taxonomy_ = taxonomy_repo.model(table_name)

    taxonomy_data = taxonomy_.get_group(sample_ids, '').to_dict()
    del taxonomy_data['name']
    response = jsonify(taxonomy_data)
    return response, 200


def resources_alt(dataset):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    ret_val = {
        'resources': taxonomy_repo.resources(),
    }
    return jsonify(ret_val), 200


def resources():
    taxonomy_repo = TaxonomyRepo()
    ret_val = {
        'resources': taxonomy_repo.resources(),
    }
    return jsonify(ret_val), 200


def single_sample_taxa_present_alt(dataset, sample_id, resource):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    sample_ids = [sample_id]
    return _present_microbes_taxonomy_table(sample_ids, resource,
                                            taxonomy_repo,
                                            )


def single_sample_taxa_present(sample_id, resource):
    sample_ids = [sample_id]
    return _present_microbes_taxonomy_table(sample_ids, resource,
                                            taxonomy_repo=TaxonomyRepo(),
                                            )


def group_taxa_present_alt(body, dataset, resource):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    sample_ids = body['sample_ids']
    return _present_microbes_taxonomy_table(sample_ids, resource,
                                            taxonomy_repo,
                                            )


def group_taxa_present(body, resource):
    sample_ids = body['sample_ids']
    return _present_microbes_taxonomy_table(sample_ids, resource,
                                            taxonomy_repo=TaxonomyRepo(),
                                            )


def _present_microbes_taxonomy_table(sample_ids, resource, taxonomy_repo):
    error_response = _check_resource_and_missing_ids(taxonomy_repo,
                                                     sample_ids, resource)
    if error_response:
        return error_response

    taxonomy_ = taxonomy_repo.model(resource)
    taxonomy_table = taxonomy_.presence_data_table(sample_ids)
    response = jsonify(taxonomy_table.to_dict())
    return response, 200


def exists_single_alt(dataset, resource, sample_id):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    return _exists(resource, sample_id, taxonomy_repo)


def exists_single(resource, sample_id):
    return _exists(resource, sample_id, taxonomy_repo=TaxonomyRepo())


def exists_group_alt(body, dataset, resource):
    taxonomy_repo = _get_taxonomy_repo(dataset)
    return _exists(resource, body, taxonomy_repo)


def exists_group(body, resource):
    return _exists(resource, body, taxonomy_repo=TaxonomyRepo())


def _exists(resource, samples, taxonomy_repo):
    available_resources = taxonomy_repo.resources()

    type_ = 'resource'
    missing_resource = validate_resource(available_resources, resource,
                                         type_)
    if missing_resource:
        return missing_resource

    return jsonify(taxonomy_repo.exists(samples, resource)), 200


def ranks_sample(dataset, resource, sample_size):
    taxonomy_repo = _get_taxonomy_repo(dataset)

    error_response = _check_resource_and_missing_ids(taxonomy_repo,
                                                     [],
                                                     resource)
    if error_response:
        return error_response

    taxonomy_ = taxonomy_repo.model(resource)
    summary = taxonomy_.ranks_sample(sample_size)
    order = taxonomy_.ranks_order(summary['Taxon'])

    payload = summary.to_dict('list')
    payload.pop('Sample ID')
    payload['Taxa-order'] = order

    return jsonify(payload), 200


def ranks_specific(dataset, resource, sample_id):
    taxonomy_repo = _get_taxonomy_repo(dataset)

    error_response = _check_resource_and_missing_ids(taxonomy_repo,
                                                     [sample_id, ],
                                                     resource)
    if error_response:
        return error_response

    taxonomy_ = taxonomy_repo.model(resource)
    summary = taxonomy_.ranks_specific(sample_id)
    order = taxonomy_.ranks_order(summary['Taxon'])

    payload = summary.to_dict('list')
    payload.pop('Sample ID')
    payload['Taxa-order'] = order

    return jsonify(payload), 200

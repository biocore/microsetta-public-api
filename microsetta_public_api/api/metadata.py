from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.utils._utils import jsonify, validate_resource


def category_values(category):
    repo = MetadataRepo()
    if category in repo.categories:
        values = repo.category_values(category)
        return jsonify(values), 200
    else:
        text = f"Metadata category: '{category}' does not exist."
        return jsonify(text=text, error=404), 404


def filter_sample_ids(taxonomy=None, alpha_metric=None, **kwargs):
    repo = MetadataRepo()
    query = _format_query(kwargs)
    is_invalid = _validate_query(kwargs, repo)
    if is_invalid:
        return is_invalid
    matching_ids = repo.sample_id_matches(query)

    matching_ids, error_code, error_response = _filter_matching_ids(
        matching_ids, TaxonomyRepo, 'resources', taxonomy, 'resource',
    )

    matching_ids, error_code, error_response = _filter_matching_ids(
        matching_ids, AlphaRepo, 'available_metrics', alpha_metric,
        'metric', error_response=error_response, error_code=error_code,
    )

    if error_response:
        return error_response, error_code

    return jsonify(sample_ids=matching_ids), 200


def filter_sample_ids_query_builder(body, taxonomy=None, alpha_metric=None):
    query = body
    repo = MetadataRepo()
    # TODO probably want some form of validation here
    matching_ids = repo.sample_id_matches(query)
    matching_ids, error_code, error_response = _filter_matching_ids(
        matching_ids, TaxonomyRepo, 'resources', taxonomy, 'resource',
    )

    matching_ids, error_code, error_response = _filter_matching_ids(
        matching_ids, AlphaRepo, 'available_metrics', alpha_metric,
        'metric', error_response=error_response, error_code=error_code,
    )

    if error_response:
        return error_response, error_code

    return jsonify(sample_ids=matching_ids), 200


def _filter_matching_ids(matching_ids, repo, category, value, resource_type,
                         error_response=None, error_code=None):
    if value is not None:
        repo_instance = repo()
        available_resources = getattr(repo_instance, category)()

        missing_resource = validate_resource(available_resources, value,
                                             resource_type)
        if missing_resource:
            error_response, error_code = missing_resource

        else:
            matching_ids_ = [id_ for id_ in matching_ids if
                             repo_instance.exists(id_, value)]
            matching_ids = matching_ids_
    return matching_ids, error_code, error_response


def _validate_query(dict_, repo):
    categories = set(repo.categories)
    for id_ in dict_:
        if id_ not in categories:
            text = f"Metadata category: '{id_}' does not exist."
            return jsonify(text=text, error=404), 404


def _format_query(dict_):
    query = dict(condition="AND", rules=[])
    for id_, value in dict_.items():
        new_rule = {
            "id": id_,
            "value": value,
            "operator": "equal",
        }
        query['rules'].append(new_rule)

    return query

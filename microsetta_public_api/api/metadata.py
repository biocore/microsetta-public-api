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

    if taxonomy is not None:
        taxonomy_repo = TaxonomyRepo()
        available_resources = taxonomy_repo.resources()

        type_ = 'resource'
        missing_resource = validate_resource(available_resources, taxonomy,
                                             type_)
        if missing_resource:
            return missing_resource

        matching_ids_ = [id_ for id_ in matching_ids if
                         taxonomy_repo.exists(id_, taxonomy)]
        matching_ids = matching_ids_

    if alpha_metric is not None:
        alpha_repo = AlphaRepo()

        # figure out if the user asked for a metric we have data on
        available_metrics = alpha_repo.available_metrics()
        type_ = 'metric'
        missing_metric = validate_resource(available_metrics, alpha_metric,
                                           type_)
        if missing_metric:
            return missing_metric

        # make sure all of the data the samples the user asked for have values
        # for the given metric
        matching_ids_ = [id_ for id_ in matching_ids if
                         alpha_repo.exists(id_, alpha_metric)]
        matching_ids = matching_ids_

    return jsonify(sample_ids=matching_ids), 200


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

from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.utils import jsonify


def category_values(category):
    repo = MetadataRepo()
    if category in repo.categories:
        values = repo.category_values(category)
        return jsonify(values), 200
    else:
        text = f"Metadata category: '{category}' does not exist."
        return jsonify(text=text, error=404), 404


def filter_sample_ids(**kwargs):
    repo = MetadataRepo()
    query = _format_query(kwargs)
    matching_ids = repo.sample_id_matches(query)
    return jsonify(sample_ids=matching_ids), 200


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

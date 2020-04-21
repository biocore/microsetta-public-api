from flask import jsonify
from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.models._exceptions import UnknownID
from microsetta_public_api.repo._alpha_repo import AlphaRepo


def get_alpha(sample_id, alpha_metric):
    alpha_repo = AlphaRepo()
    try:
        alpha_series = alpha_repo.get_alpha_diversity(sample_id, alpha_metric)
    except UnknownID:
        return jsonify(error=404, text="Sample ID not found."), 404
    alpha_ = Alpha(alpha_series)
    ret_val = alpha_.get_group_raw().to_dict()

    return jsonify(ret_val), 200

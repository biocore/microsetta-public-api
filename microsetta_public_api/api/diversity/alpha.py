from flask import jsonify
from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.repo._alpha_repo import AlphaRepo


def get_alpha(sample_id, alpha_metric):
    alpha_repo = AlphaRepo()
    if not all(alpha_repo.exists([sample_id])):
        return jsonify(error=404, text="Sample ID not found."), 404
    alpha_series = alpha_repo.get_alpha_diversity([sample_id],
                                                  alpha_metric)
    alpha_ = Alpha(alpha_series)
    alpha_data = alpha_.get_group_raw().to_dict()
    ret_val = {
        'sample_id': sample_id,
        'alpha_metric': alpha_data['alpha_metric'],
        'data': alpha_data['data'][sample_id],

    }

    return jsonify(ret_val), 200

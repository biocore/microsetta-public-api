from flask import jsonify


def get_alpha(sample_id, alpha_metric):
    ret_val = {
        'sample_id': sample_id,
        'alpha_metric': alpha_metric,
        'value': 8.25,
    }
    return jsonify(ret_val), 200

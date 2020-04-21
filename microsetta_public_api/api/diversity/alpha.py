import pandas as pd
from flask import jsonify
from microsetta_public_api.models._alpha import Alpha


def get_alpha(sample_id, alpha_metric):
    # TODO have some function grab this data from somewhere else
    alpha_series = pd.Series({sample_id: 8.25}, name=alpha_metric)

    alpha_ = Alpha(alpha_series)
    ret_val = alpha_.get_group_raw().to_dict()

    return jsonify(ret_val), 200

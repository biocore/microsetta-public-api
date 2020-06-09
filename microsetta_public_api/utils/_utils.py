from flask import jsonify as flask_jsonify


def jsonify(*args, **kwargs):
    return flask_jsonify(*args, **kwargs)


def validate_resource(available, name, type_):
    if name not in available:
        return jsonify(error=404,
                       text=f"Requested {type_}: '{name}' "
                            f"is unavailable. Available {type_}(s): "
                            f"{available}"), 404


def check_missing_ids(missing_ids, alpha_metric, type_):
    if len(missing_ids) > 0:
        return jsonify(missing_ids=missing_ids,
                       error=404, text=f"Sample ID(s) not found for "
                                       f"{type_}: {alpha_metric}"), \
               404

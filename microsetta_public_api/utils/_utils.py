from flask import jsonify as flask_jsonify


def jsonify(*args, **kwargs):
    return flask_jsonify(*args, **kwargs)

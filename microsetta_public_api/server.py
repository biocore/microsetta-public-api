from pkg_resources import resource_filename
import copy
from microsetta_public_api.config import (
    SERVER_CONFIG,
    resources as config_resources,
    schema,
    DictElement,
)
from microsetta_public_api.resources import resources
from microsetta_public_api.resources_alt import resources_alt
from microsetta_public_api.resources_alt import Q2Visitor
from microsetta_public_api.exceptions import (UnknownMetric,
                                              UnknownResource,
                                              UnknownID,
                                              InvalidParameter,
                                              UnknownCategory,
                                              IncompatibleOptions,
                                              )
from flask import jsonify
from flask.json import JSONEncoder
from concurrent.futures import ThreadPoolExecutor
import numpy as np

import connexion
from flask_cors import CORS


class NumPySafeJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        else:
            return super().default(obj)


class ErrorHandlerFactory:

    @staticmethod
    def get_method(code):
        def handler(e):
            return jsonify(text=str(e), code=code), code
        return handler


handle_400 = ErrorHandlerFactory.get_method(400)
handle_404 = ErrorHandlerFactory.get_method(404)

_pool = ThreadPoolExecutor()
futures = set()


def atomic_update_resources(resource):
    # create a new element to store the data in
    element = DictElement()
    element.update(resource)
    visitor = Q2Visitor()
    element.accept(visitor)
    # after data has been loaded by the q2 visitor, update resources_alt
    #  so that it is accessible.
    # Updating resources_alt from another element means the server will
    #  not show the skeleton of any unloaded data to the client
    resources_alt.update(element)


def build_app():
    app = connexion.FlaskApp(__name__)
    app.app.json_encoder = NumPySafeJSONEncoder

    resource_config = SERVER_CONFIG.get('resources', {})

    # default configuration for resources is provided in
    # microsetta.config.resources, this config can be updated by a json file
    # passed to `build_app`.
    config_resources.update(resource_config)
    resources.update(config_resources)
    resource = copy.deepcopy(config_resources)
    resource = schema.make_elements(resource)
    load_data = _pool.submit(atomic_update_resources, resource)
    futures.add(load_data)
    load_data.add_done_callback(lambda fut: futures.remove(load_data))

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')

    # validate_responses needs to be False to support sending binary
    # files it seems, see https://github.com/zalando/connexion/issues/401
    app.add_api(app_file, validate_responses=SERVER_CONFIG.get('validate',
                                                               True))

    app.app.register_error_handler(UnknownMetric, handle_404)
    app.app.register_error_handler(UnknownResource, handle_404)
    app.app.register_error_handler(UnknownID, handle_404)
    app.app.register_error_handler(UnknownCategory, handle_404)
    app.app.register_error_handler(IncompatibleOptions, handle_400)
    app.app.register_error_handler(InvalidParameter, handle_400)

    CORS(app.app)

    return app


def run(app):
    app.run(
        port=SERVER_CONFIG['port'],
        debug=SERVER_CONFIG['debug'],
    )


if __name__ == "__main__":
    use_test_database = SERVER_CONFIG['use_test_database']
    if use_test_database:
        # import TestDatabase here to avoid circular import
        from microsetta_public_api.utils.testing import TestDatabase
        import atexit
        tdb = TestDatabase()
        tdb.start()
        atexit.register(tdb.stop)
        app = build_app()
        run(app)
        tdb.stop()
    else:
        app = build_app()
        run(app)

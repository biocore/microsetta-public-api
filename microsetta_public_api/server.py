from pkg_resources import resource_filename
import copy
from microsetta_public_api.config import (
    SERVER_CONFIG,
    resources as config_resources,
    schema,
)
from microsetta_public_api.resources import resources
from microsetta_public_api.resources_alt import resources_alt
from microsetta_public_api.resources_alt import Q2Visitor
from microsetta_public_api.exceptions import (UnknownMetric,
                                              UnknownResource,
                                              UnknownID,
                                              IncompatibleOptions,
                                              )
from flask import jsonify

import connexion
from flask_cors import CORS


class ErrorHandlerFactory:

    @staticmethod
    def get_method(code):
        def handler(e):
            return jsonify(text=str(e), code=code), code
        return handler


handle_400 = ErrorHandlerFactory.get_method(400)
handle_404 = ErrorHandlerFactory.get_method(404)


def build_app():
    app = connexion.FlaskApp(__name__)

    resource_config = SERVER_CONFIG.get('resources', {})

    # default configuration for resources is provided in
    # microsetta.config.resources, this config can be updated by a json file
    # passed to `build_app`.
    config_resources.update(resource_config)
    resources.update(config_resources)
    resource = copy.deepcopy(config_resources)
    resource = schema.make_elements(resource)
    resources_alt.update(resource)
    resources_alt.accept(Q2Visitor())

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    app.app.register_error_handler(UnknownMetric, handle_404)
    app.app.register_error_handler(UnknownResource, handle_404)
    app.app.register_error_handler(UnknownID, handle_404)
    app.app.register_error_handler(IncompatibleOptions, handle_400)

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

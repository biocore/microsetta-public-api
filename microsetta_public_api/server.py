from pkg_resources import resource_filename
from microsetta_public_api.config import (SERVER_CONFIG,
                                          resources as config_resources)
from microsetta_public_api.resources import resources

import connexion
from flask_cors import CORS


def build_app():
    app = connexion.FlaskApp(__name__)

    resource_config = SERVER_CONFIG.get('resources', {})

    # default configuration for resources is provided in
    # microsetta.config.resources, this config can be updated by a json file
    # passed to `build_app`.
    config_resources.update(resource_config)
    resources.update(config_resources)

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    CORS(app.app)

    return app


def run(app):
    app.run(
        port=SERVER_CONFIG['port'],
        debug=SERVER_CONFIG['debug'],
        use_reloader=SERVER_CONFIG.get('use_reloader', True)
    )


if __name__ == "__main__":
    use_test_database = SERVER_CONFIG['use_test_database']
    if use_test_database:
        # import TestDatabase here to avoid circular import
        from microsetta_public_api.utils.testing import TestDatabase
        with TestDatabase():
            app = build_app()
            run(app)
    else:
        app = build_app()
        run(app)

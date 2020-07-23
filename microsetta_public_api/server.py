import json
from pkg_resources import resource_filename
from microsetta_public_api import config
from microsetta_public_api.resources import resources

import connexion
from flask_cors import CORS


def build_app(resource_updates=None):
    app = connexion.FlaskApp(__name__)

    # default configuration for resources is provided in
    # microsetta.config.resources, this config can be updated by a json file
    # passed to `build_app`.
    if resource_updates is not None:
        config.resources.update(resource_updates)

        resources.update(config.resources)

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    CORS(app.app)

    return app


if __name__ == "__main__":
    import sys
    config_fp = sys.argv[1] if len(sys.argv) > 1 else None

    if config_fp is None:
        resource_config = None
        server_config = {}
    else:
        with open(config_fp) as fp:
            server_config = json.load(fp)
        resource_config = config['resources']

    port = server_config.get('port', 8084)
    if config_fp:
        app = build_app(resource_updates=resource_config)
        app.run(port=port, debug=True)
    else:
        # import TestDatabase here to avoid circular import
        from microsetta_public_api.utils.testing import TestDatabase
        with TestDatabase():
            app = build_app()
            app.run(port=port, debug=True)

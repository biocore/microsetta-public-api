import json
from pkg_resources import resource_filename
from microsetta_public_api import config
from microsetta_public_api.resources import resources

import connexion


def build_app(resources_config_json=None):
    app = connexion.FlaskApp(__name__)

    # default configuration for resources is provided in
    # microsetta.config.resources, this config can be updated by a json file
    # passed to `build_app`.
    if resources_config_json is not None:
        with open(resources_config_json) as fp:
            resource_updates = json.load(fp)
        config.resources.update(resource_updates)

        resources.update(config.resources)

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    return app


if __name__ == "__main__":
    import sys
    config_fp = sys.argv[1] if len(sys.argv) > 1 else None
    PORT = 8084
    if config_fp:
        app = build_app(resources_config_json=config_fp)
        app.run(port=PORT, debug=True)
    else:
        # import TestDatabase here to avoid circular import
        from microsetta_public_api.utils.testing import TestDatabase
        with TestDatabase():
            app = build_app()
            app.run(port=PORT, debug=True)

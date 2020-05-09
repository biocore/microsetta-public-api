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
        resource_updates = json.load(resources_config_json)
        config.resources.update(resource_updates)

        resources.update(config.resources)

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    return app


if __name__ == "__main__":
    app = build_app()
    app.run(port=8083, debug=True)

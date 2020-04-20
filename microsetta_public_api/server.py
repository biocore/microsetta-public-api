from pkg_resources import resource_filename

import connexion


def build_app():
    app = connexion.FlaskApp(__name__)
    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    return app


if __name__ == "__main__":
    app = build_app()
    app.run(port=8083, debug=True)

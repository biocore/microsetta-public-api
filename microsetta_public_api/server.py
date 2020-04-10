import connexion


def build_app():
    app = connexion.FlaskApp(__name__)

    app.add_api('api/microsetta_public_api.yml', validate_responses=True)

    return app


if __name__ == "__main__":
    app = build_app()
    app.run(port=8083, debug=True)

from flask import Flask

from server_c.config import Config
from server_c.extensions import db, migrate, jwt
from server_c.models import User, EmailVerificationToken
from server_c.routes import api


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(api)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
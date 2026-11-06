from flask import Flask

from server_y.config import Config
from server_y.extensions import db, migrate, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from server_y import models
    from server_y.routes import bp

    app.register_blueprint(bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5001, debug=True)
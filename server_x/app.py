from flask import Flask

from server_x.config import Config
from server_x.extensions import db, migrate, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from server_x import models
    from server_x.routes import bp
    
    app.register_blueprint(bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5002, debug=True)
from flask import Flask

from web.nav import ACCOUNT_NAV
from web.operator_help import bp as operator_help_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(operator_help_bp)
    app.config["ACCOUNT_NAV"] = ACCOUNT_NAV
    return app

import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

from core.configuration.configuration import get_app_version
from core.managers.config_manager import ConfigManager
from core.managers.error_handler_manager import ErrorHandlerManager
from core.managers.logging_manager import LoggingManager
from core.managers.module_manager import ModuleManager

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="development"):
    app = Flask(__name__)

    # Load configuration according to environment
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register modules
    module_manager = ModuleManager(app)
    module_manager.register_modules()

    @app.before_request
    def validate_session():
        from flask_login import current_user, logout_user
        from flask import session, redirect, url_for, request

        # Skip validation for 2FA endpoints and auth-related endpoints
        excluded_routes = ['auth.two_factor_verify', 'auth.two_factor_setup', 'auth.two_factor_qrcode', 'auth.two_factor_confirm', 'auth.logout', 'auth.login', 'auth.show_signup_form']
        if request.endpoint in excluded_routes:
            return

        if current_user.is_authenticated:
            from app.modules.auth.services import SessionDeviceService

            session_device_service = SessionDeviceService()
            session_id = session.get('device_session_id')

            # If no session ID, allow the request (user just logged in)
            if not session_id:
                return

            current_session = session_device_service.get_current_session(current_user.id)
            if not current_session:
                logout_user()
                return redirect(url_for('auth.login'))

    # Register login manager
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.modules.auth.models import User

        return User.query.get(int(user_id))

    # Set up logging
    logging_manager = LoggingManager(app)
    logging_manager.setup_logging()

    # Initialize error handler manager
    error_handler_manager = ErrorHandlerManager(app)
    error_handler_manager.register_error_handlers()

    # Injecting environment variables into jinja context
    @app.context_processor
    def inject_vars_into_jinja():
        return {
            "FLASK_APP_NAME": os.getenv("FLASK_APP_NAME"),
            "FLASK_ENV": os.getenv("FLASK_ENV"),
            "DOMAIN": os.getenv("DOMAIN", "localhost"),
            "APP_VERSION": get_app_version(),
        }

    # CONFIG DE CORREO
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'componenteshub@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ocbz rucd onqg qvwo'
    app.config['MAIL_DEFAULT_SENDER'] = 'componenteshub@gmail.com'

    mail = Mail()
    mail.init_app(app)

    return app


app = create_app()

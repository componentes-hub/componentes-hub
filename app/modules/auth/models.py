from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from user_agents import parse
import uuid


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    totp_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)

    data_sets = db.relationship("DataSet", backref="user", lazy=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False)
    sessions = db.relationship("SessionDevice", backref="user", lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if "password" in kwargs:
            self.set_password(kwargs["password"])

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def temp_folder(self) -> str:
        from app.modules.auth.services import AuthenticationService

        return AuthenticationService().temp_folder_by_user(self)


class SessionDevice(db.Model):
    __mapper_args__ = {
        "confirm_deleted_rows": False
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Device info
    device_type = db.Column(db.String(50), nullable=False)  # mobile, desktop, tablet
    browser = db.Column(db.String(100), nullable=False)
    os = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_activity = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_current = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<SessionDevice {self.get_display_name()}>"

    def get_display_name(self):
        return f"{self.browser} en {self.os}"

    def to_dict(self):
        return {
            'id': self.id,
            'session_token': self.session_token,
            'display_name': self.get_display_name(),
            'default_name': f"{self.browser} en {self.os}",
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_current': self.is_current
        }

    @staticmethod
    def create_from_request(user_id, request):
        user_agent = request.headers.get('User-Agent', '')
        ua = parse(user_agent)

        # Determinar tipo de dispositivo
        if ua.is_mobile:
            device_type = 'mobile'
        elif ua.is_tablet:
            device_type = 'tablet'
        else:
            device_type = 'desktop'

        session = SessionDevice(
            user_id=user_id,
            device_type=device_type,
            browser=ua.browser.family,
            os=ua.os.family,
            ip_address=request.remote_addr,
            user_agent=user_agent
        )

        return session

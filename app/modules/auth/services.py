import os

from flask_login import current_user, login_user
from flask import session as flask_session

from app.modules.auth.models import User, SessionDevice
from app.modules.auth.repositories import UserRepository, SessionDeviceRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

from datetime import datetime, timezone


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            return True
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))


class SessionDeviceService(BaseService):

    def __init__(self):
        super().__init__(SessionDeviceRepository())

    def create_session(self, user_id, request):
        session_device = SessionDevice.create_from_request(user_id, request)

        self.repository.session.add(session_device)
        self.repository.session.commit()

        # Save token in flask session
        flask_session['device_session_id'] = session_device.id
        flask_session['device_session_token'] = session_device.session_token
        flask_session.permanent = True

        return session_device

    def get_user_sessions(self, user_id):
        return SessionDevice.query.filter_by(user_id=user_id).order_by(
            SessionDevice.last_activity.desc()
        ).all()

    def get_current_session(self, user_id):
        session_id = flask_session.get('device_session_id')
        if session_id:
            return self.repository.get_by(id=session_id, user_id=user_id)
        return None

    def update_last_activity(self, session_id):
        if not session_id:
            return

        session = self.repository.get(session_id)
        if session:
            session.last_activity = datetime.now(timezone.utc)
            self.repository.session.commit()

    def close_session(self, session_id, user_id):
        session = self.repository.get_by(id=session_id, user_id=user_id)

        if session:
            self.repository.delete(session_id)
            self.repository.session.commit()
            return True
        return False

    def close_all_other_sessions(self, user_id):
        current_session_id = flask_session.get('device_session_id')

        sessions_to_close = SessionDevice.query.filter(
            SessionDevice.user_id == user_id,
            SessionDevice.id != current_session_id
        ).all()

        count = len(sessions_to_close)
        for session in sessions_to_close:
            self.repository.delete(session.id)
        self.repository.session.commit()

        return count

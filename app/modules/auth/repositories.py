from app.modules.auth.models import User, SessionDevice
from core.repositories.BaseRepository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def create(self, commit: bool = True, **kwargs):
        password = kwargs.pop("password")
        instance = self.model(**kwargs)
        instance.set_password(password)
        self.session.add(instance)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return instance

    def get_by_email(self, email: str):
        return self.model.query.filter_by(email=email).first()


class SessionDeviceRepository(BaseRepository):
    def __init__(self):
        super().__init__(SessionDevice)

    def get_by(self, **kwargs):
        return self.model.query.filter_by(**kwargs).first()

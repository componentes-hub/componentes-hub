import pytest
from flask import url_for
from app import db

from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService, SessionDeviceService
from app.modules.profile.repositories import UserProfileRepository
from app.modules.auth.models import SessionDevice


@pytest.fixture(scope="module")
def test_client(test_client):
    yield test_client


@pytest.fixture(scope="function")
def test_user(test_client):
    with test_client.application.app_context():
        repo = UserRepository()
        user = repo.get_by_email("session_test@example.com")

        if not user:
            auth_service = AuthenticationService()
            data = {
                "name": "Test",
                "surname": "User",
                "email": "session_test@example.com",
                "password": "test1234"
            }
            auth_service.create_with_profile(**data)
            db.session.commit()
            user = repo.get_by_email("session_test@example.com")

        return user


def test_login_success(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login", data=dict(email="bademail@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="basspassword"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup", data=dict(surname="Foo", email="test@example.com", password="test1234"), follow_redirects=True
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


def test_signup_user_unsuccessful(test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup", data=dict(name="Test", surname="Foo", email=email, password="test1234"), follow_redirects=True
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert f"Email {email} in use".encode("utf-8") in response.data


def test_signup_user_successful(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="Foo", surname="Example", email="foo@example.com", password="foo1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("public.index"), "Signup was unsuccessful"


def test_service_create_with_profie_success(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "service_test@example.com", "password": "test1234"}

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "test@example.com", "password": ""}

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


# ------------------------------ SESSSIONS TESTS -------------------------------------- #


def test_create_session_on_signup(test_client, test_user):
    # IMPORTANTE: Asegurarse de que no hay sesión activa de tests anteriores
    test_client.get("/logout", follow_redirects=True)

    email = "signup_session_test@example.com"

    # Limpiar usuario si existe de tests anteriores
    with test_client.application.app_context():
        existing_user = UserRepository().get_by_email(email)
        if existing_user:
            SessionDevice.query.filter_by(user_id=existing_user.id).delete()
            from app.modules.profile.models import UserProfile
            profile = UserProfile.query.filter_by(user_id=existing_user.id).first()
            if profile:
                db.session.delete(profile)
            db.session.delete(existing_user)
            db.session.commit()

    response = test_client.post(
        "/signup",
        data=dict(
            name="New",
            surname="User",
            email=email,
            password="password123"
        ),
        follow_redirects=True
    )

    assert response.status_code == 200
    assert response.request.path == url_for("public.index"), \
        f"Signup failed. Redirected to: {response.request.path}"

    with test_client.application.app_context():
        user = UserRepository().get_by_email(email)
        assert user is not None, "El usuario no se creó correctamente"

        sessions = SessionDevice.query.filter_by(user_id=user.id).all()
        assert len(sessions) == 1, f"Expected 1 session, found {len(sessions)}"

    test_client.get("/logout", follow_redirects=True)


def test_get_user_sessions(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    session_service = SessionDeviceService()
    sessions = session_service.get_user_sessions(test_user.id)
    assert len(sessions) == 1
    assert sessions[0].user_id == test_user.id

    test_client.get("/logout", follow_redirects=True)


def test_get_current_session(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    session_service = SessionDeviceService()
    current_session = session_service.get_current_session(test_user.id)
    assert current_session is not None
    assert current_session.user_id == test_user.id

    test_client.get("/logout", follow_redirects=True)


def test_get_current_session_not_authenticated(test_user):
    session_service = SessionDeviceService()
    current_session = session_service.get_current_session(test_user.id)
    assert current_session is None


def test_close_session_successful(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    session_service = SessionDeviceService()
    sessions = session_service.get_user_sessions(test_user.id)
    session_id = sessions[0].id

    result = session_service.close_session(session_id, test_user.id)
    assert result is True

    remaining_sessions = session_service.get_user_sessions(test_user.id)
    assert len(remaining_sessions) == 0

    test_client.get("/logout", follow_redirects=True)


def test_close_session_not_found(test_user):
    session_service = SessionDeviceService()
    result = session_service.close_session(99999, test_user.id)
    assert result is False


def test_close_session_via_route(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    sessions = SessionDevice.query.filter_by(user_id=test_user.id).all()
    session_id = sessions[0].id

    response = test_client.delete(f"/sessions/{session_id}")
    assert response.status_code == 400
    assert b"Use the logout button" in response.data

    test_client.get("/logout", follow_redirects=True)


def test_show_sessions_page_authenticated(test_client):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    response = test_client.get("/sessions")
    assert response.status_code == 200
    assert b"Active Sessions" in response.data or b"Active devices" in response.data

    test_client.get("/logout", follow_redirects=True)


def test_show_sessions_page_not_authenticated(test_client):
    response = test_client.get("/sessions", follow_redirects=True)
    assert response.request.path == url_for("auth.login")


def test_show_sessions_displays_current_badge(test_client):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    response = test_client.get("/sessions")
    assert b"Current session" in response.data

    test_client.get("/logout", follow_redirects=True)


def test_logout_deletes_session(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True
    )

    session_service = SessionDeviceService()

    sessions_before = session_service.get_user_sessions(test_user.id)
    assert len(sessions_before) == 1

    test_client.get("/logout", follow_redirects=True)

    sessions_after = session_service.get_user_sessions(test_user.id)
    assert len(sessions_after) == 0

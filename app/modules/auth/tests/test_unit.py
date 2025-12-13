import pytest
from flask import url_for
from app import db

from app.modules.auth.repositories import UserRepository, SessionDeviceRepository
from app.modules.auth.services import AuthenticationService, SessionDeviceService
from app.modules.profile.repositories import UserProfileRepository
from app.modules.auth.models import SessionDevice, User
from app.modules.profile.models import UserProfile


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
    test_client.get("/logout", follow_redirects=True)

    email = "signup_session_test@example.com"

    # Limpiar usuario si existe de tests anteriores
    with test_client.application.app_context():
        existing_user = UserRepository().get_by_email(email)
        if existing_user:
            SessionDevice.query.filter_by(user_id=existing_user.id).delete()
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


def test_session_device_properties(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    with test_client.application.app_context():
        sess = SessionDevice.query.filter_by(user_id=test_user.id).first()
        assert sess is not None
        assert isinstance(sess.user_agent, str) and len(sess.user_agent) > 0
        assert isinstance(sess.ip_address, str) and len(sess.ip_address) > 0
        assert isinstance(sess.session_token, str) and len(sess.session_token) > 0
        assert sess.created_at is not None
        assert sess.last_activity is not None
        assert sess.user_id == test_user.id

    test_client.get("/logout", follow_redirects=True)


def test_session_service_get_by_token(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    with test_client.application.app_context():
        sess = SessionDevice.query.filter_by(user_id=test_user.id).first()
        assert sess is not None
        token = sess.session_token
        found = SessionDevice.query.filter_by(session_token=token).first()
        assert found is not None
        assert found.id == sess.id

    test_client.get("/logout", follow_redirects=True)


def test_multiple_sessions_manual_creation(test_client, test_user):
    with test_client.application.app_context():
        # crear 3 sesiones manualmente
        s_objs = []
        for i in range(3):
            sd = SessionDevice(
                user_id=test_user.id,
                session_token=f"manual-token-{i}",
                device_type="desktop",
                browser=f"Browser{i}",
                os=f"OS{i}",
                ip_address=f"10.0.0.{i}",
                user_agent=f"Agent {i}"
            )
            db.session.add(sd)
            s_objs.append(sd)
        db.session.commit()

        service = SessionDeviceService()
        sessions = service.get_user_sessions(test_user.id)
        # Puede haber más sesiones si hubo login previo; comprobamos que existan al menos las 3 nuevas
        tokens = {s.session_token for s in sessions}
        for i in range(3):
            assert f"manual-token-{i}" in tokens

        # limpiar las que hemos añadido
        SessionDevice.query.filter(
            SessionDevice.session_token.in_([f"manual-token-{i}" for i in range(3)])
        ).delete(synchronize_session=False)
        db.session.commit()


def test_close_all_other_sessions_route_and_service(test_client, test_user):
    # Primero aseguramos logout y login para entorno limpio
    test_client.get("/logout", follow_redirects=True)

    # Login normal para crear una sesión actual
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    with test_client.application.app_context():
        sd_extra = SessionDevice(
            user_id=test_user.id,
            session_token="extra-token-close-1",
            device_type="desktop",
            browser="ExtraBrowser",
            os="ExtraOS",
            ip_address="192.0.2.1",
            user_agent="ExtraAgent"
        )
        db.session.add(sd_extra)
        db.session.commit()

        current = SessionDevice.query.filter_by(user_id=test_user.id).order_by(SessionDevice.created_at.asc()).first()

    with test_client.session_transaction() as s:
        s["device_session_id"] = current.id
        s["device_session_token"] = current.session_token

    response = test_client.post("/sessions/close-all-others", follow_redirects=True)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data is not None
    assert "closed_count" in json_data or "closed" in json_data or "closed_count" in json_data.get("message", "")

    with test_client.application.app_context():
        remaining = SessionDevice.query.filter_by(user_id=test_user.id).all()
        # Solo debería quedar la actual (current.id)
        ids = [r.id for r in remaining]
        assert current.id in ids
        # limpiar todo
        SessionDevice.query.filter_by(user_id=test_user.id).delete()
        db.session.commit()


def test_delete_other_user_session_via_route(test_client, test_user):
    with test_client.application.app_context():
        other = User(email="other_for_delete@example.com", password="otherpass")
        db.session.add(other)
        db.session.commit()

        other_sess = SessionDevice(
            user_id=other.id,
            session_token="other-session-token",
            device_type="desktop",
            browser="OtherBrowser",
            os="OtherOS",
            ip_address="198.51.100.2",
            user_agent="OtherAgent"
        )
        db.session.add(other_sess)
        db.session.commit()
        other_id = other.id
        other_sess_id = other_sess.id

    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    # Intentar borrar la sesión del otro usuario
    res = test_client.delete(f"/sessions/{other_sess_id}", follow_redirects=True)
    assert res.status_code in (400, 401, 403, 404)

    # Comprobar que la sesión del otro usuario sigue en BD
    with test_client.application.app_context():
        still = SessionDevice.query.get(other_sess_id)
        assert still is not None

        # limpiar
        SessionDevice.query.filter_by(user_id=other_id).delete()
        db.session.delete(User.query.get(other_id))
        db.session.commit()

    test_client.get("/logout", follow_redirects=True)


def test_session_cleanup_on_user_delete(test_client):
    with test_client.application.app_context():
        temp = User(email="temp_user_cleanup@example.com", password="tmppass")
        db.session.add(temp)
        db.session.commit()
        temp_id = temp.id

        # crear sesión
        sd = SessionDevice(
            user_id=temp_id,
            session_token="temp-clean-token",
            device_type="desktop",
            browser="TmpB",
            os="TmpOS",
            ip_address="203.0.113.5",
            user_agent="TmpAgent"
        )
        db.session.add(sd)
        db.session.commit()

        assert SessionDevice.query.filter_by(user_id=temp_id).count() == 1

        # borrar usuario
        db.session.delete(temp)
        db.session.commit()

        assert SessionDevice.query.filter_by(user_id=temp_id).count() == 0


def test_update_last_activity_service(test_client, test_user):
    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    with test_client.application.app_context():
        sess = SessionDevice.query.filter_by(user_id=test_user.id).first()
        assert sess is not None
        original = sess.last_activity

        service = SessionDeviceService()
        service.update_last_activity(sess.id)

        repository = SessionDeviceRepository()
        updated = repository.get_by(id=sess.id)

        assert updated is not None
        assert updated.last_activity is not None
        assert updated.last_activity >= original


def test_session_browser_and_ip_captured_from_request(test_client, test_user):
    headers = {"User-Agent": "UnitTestAgent/1.2 (Chrome)"}
    environ_overrides = {"REMOTE_ADDR": "123.45.67.89"}

    test_client.post(
        "/login",
        data=dict(email="session_test@example.com", password="test1234"),
        headers=headers,
        environ_overrides=environ_overrides,
        follow_redirects=True,
    )

    with test_client.application.app_context():
        sess = SessionDevice.query.filter_by(user_id=test_user.id).first()
        assert sess is not None
        assert sess.user_agent is not None
        assert len(sess.user_agent) > 0
        assert sess.ip_address is not None

    test_client.get("/logout", follow_redirects=True)


def test_session_routes_require_login(test_client):
    routes = [
        ("GET", "/sessions"),
        ("GET", "/sessions/current"),
        ("DELETE", "/sessions/1"),
        ("POST", "/sessions/close-all-others"),
    ]

    for method, route in routes:
        res = test_client.open(route, method=method)
        assert res.status_code in (401, 302)


def test_cannot_close_current_session(test_client, test_user):
    test_client.post("/login", data={
        "email": "session_test@example.com",
        "password": "test1234"
    })

    with test_client.application.app_context():
        sess = SessionDevice.query.filter_by(user_id=test_user.id).first()

    res = test_client.delete(f"/sessions/{sess.id}")
    assert res.status_code == 400


def test_close_nonexistent_session(test_client, test_user):
    test_client.post("/login", data={
        "email": "session_test@example.com",
        "password": "test1234"
    })

    res = test_client.delete("/sessions/99999")
    assert res.status_code == 404

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType

import uuid
user = User(email=f"user_{uuid.uuid4()}@example.com", password="test1234")


@pytest.fixture(autouse=True)
def clean_db():
    yield
    db.session.rollback()


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        user_test = User(email="user@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

    yield test_client


def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get("/profile/edit")
    assert response.status_code == 200, "The profile editing page could not be accessed."
    assert b"Edit profile" in response.data, "The expected content is not present on the page"

    logout(test_client)


@pytest.fixture(scope='function')
def setup_data(test_client):
    """Crea datos de prueba y devuelve sus IDs"""
    with test_client.application.app_context():
        unique_email = f"user_{uuid.uuid4()}@example.com"
        user = User(email=unique_email, password="test1234")
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(user_id=user.id, name="Test", surname="User")
        db.session.add(profile)
        db.session.commit()

        author = Author(name="Author Test")
        db.session.add(author)
        db.session.commit()

        ds_meta_data = DSMetaData(
            title="Dataset Test",
            description="Dataset description",
            publication_type=PublicationType.NONE
        )
        ds_meta_data.authors.append(author)
        db.session.add(ds_meta_data)
        db.session.commit()

        dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_data.id)
        db.session.add(dataset)
        db.session.commit()

        # Devuelve solo los IDs
        return {
            "user_id": user.id,
            "profile_id": profile.id,
            "author_id": author.id,
            "dataset_id": dataset.id,
            "ds_meta_data_id": ds_meta_data.id
        }


def test_proyectos_usuario_page(test_client, setup_data):
    """GET /user/<id>/projects devuelve datasets del usuario"""
    from app.modules.profile.models import UserProfile

    # Usamos el ID del profile, no del user
    user_profile = UserProfile.query.get(setup_data["profile_id"])
    assert user_profile is not None, "UserProfile no encontrado en la base de datos de test"

    response = test_client.get(f"/user/{user_profile.id}/projects")
    assert response.status_code == 200


def test_proyectos_autor_page(test_client, setup_data):
    """GET /author/<id>/projects devuelve datasets del autor"""
    from app.modules.dataset.models import Author

    author = Author.query.get(setup_data["author_id"])
    response = test_client.get(f"/author/{author.id}/projects")
    assert response.status_code == 200
    assert b"Dataset Test" in response.data


def test_proyectos_usuario_no_encontrado(test_client):
    """Usuario inexistente devuelve 404"""
    response = test_client.get("/user/999999/projects")
    assert response.status_code == 404
    assert b"Autor no encontrado" in response.data


def test_proyectos_autor_no_encontrado(test_client):
    """Autor inexistente devuelve 404"""
    response = test_client.get("/author/999999/projects")
    assert response.status_code == 404
    assert b"Autor no encontrado" in response.data

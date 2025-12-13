from types import SimpleNamespace
from unittest.mock import patch
from urllib import response
import pytest

from app import db
from app.modules.auth.models import User
from app.modules.community.models import Community, CommunityFollower
from app.modules.community.services import CommunityUserService
from app.modules.conftest import login, logout
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.models import UserFollowAuthor, UserFollowUser, UserProfile
from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType

import uuid

from app.modules.profile.repositories import UserProfileRepository
from app.modules.profile.services import UserProfileService

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


def test_user_projects_page(test_client, setup_data):
    """GET /user/<id>/projects devuelve datasets del usuario"""
    from app.modules.profile.models import UserProfile

    # Usamos el ID del profile, no del user
    user_profile = UserProfile.query.get(setup_data["profile_id"])
    assert user_profile is not None, "UserProfile no encontrado en la base de datos de test"

    response = test_client.get(f"/user/{user_profile.id}/projects")
    assert response.status_code == 200


def test_author_projects_page(test_client, setup_data):
    """GET /author/<id>/projects devuelve datasets del autor"""
    from app.modules.dataset.models import Author

    author = Author.query.get(setup_data["author_id"])
    response = test_client.get(f"/author/{author.id}/projects")
    assert response.status_code == 200
    assert b"Dataset Test" in response.data


def test_user_projects_page_not_found(test_client):
    """Usuario inexistente devuelve 404"""
    response = test_client.get("/user/999999/projects")
    assert response.status_code == 404


def test_author_projects_page_not_found(test_client):
    """Autor inexistente devuelve 404"""
    response = test_client.get("/author/999999/projects")
    assert response.status_code == 404


def test_user_profile_repository_create(user):
    repo = UserProfileRepository()

    profile = repo.create(
        user_id=user.id,
        name="John",
        surname="Doe"
    )

    assert profile.id is not None
    assert profile.user_id == user.id
    
    
def test_user_profile_form_orcid_validation(test_client):
    # ORCID válido
    response = test_client.post(
        "/profile/edit", 
        data={
            "name": "Test",
            "surname": "User",
            "orcid": "0000-0002-1825-0097"
        }
    )
    # Crear el formulario con request.form de la request POST
    with test_client.application.test_request_context("/profile/edit", method="POST", data=response.request.form):
        form = UserProfileForm()
        assert form.validate() is True

    # ORCID inválido (formato incorrecto)
    response = test_client.post(
        "/profile/edit",
        data={
            "name": "Test",
            "surname": "User",
            "orcid": "0000-0002-1825-009"
        }
    )
    with test_client.application.test_request_context("/profile/edit", method="POST", data=response.request.form):
        form = UserProfileForm()
        assert form.validate() is False
        assert "Invalid ORCID format" in form.orcid.errors

    # ORCID inválido (caracteres no numéricos)
    response = test_client.post(
        "/profile/edit",
        data={
            "name": "Test",
            "surname": "User",
            "orcid": "0000-0002-1825-ABCD"
        }
    )
    with test_client.application.test_request_context("/profile/edit", method="POST", data=response.request.form):
        form = UserProfileForm()
        assert form.validate() is False
        assert "Invalid ORCID format" in form.orcid.errors

# Crear un usuario para cada test evitando duplicados
@pytest.fixture
def user():
    unique_email = f"user_test_{uuid.uuid4()}@example.com"
    u = User(email=unique_email, password="123456")
    db.session.add(u)
    db.session.commit()
    return u


def test_user_profile_service_update_profile_valid(user, test_app):
    repo = UserProfileRepository()
    instance = repo.create(user_id=user.id, name="Old", surname="Name")

    with test_app.test_request_context():
        form = UserProfileForm(
            name="NewName",
            surname="NewSurname",
            meta={'csrf': False} 
        )

        service = UserProfileService()
        result, errors = service.update_profile(instance.id, form)

        assert errors is None
        assert result.name == "NewName"
        assert result.surname == "NewSurname"


def test_user_profile_service_update_profile_invalid(user, test_app):
    with test_app.test_request_context():
        repo = UserProfileRepository()
        instance = repo.create(user_id=user.id, name="Old", surname="Name")

        form = UserProfileForm(
            name="",  # inválido
            surname="ValidSurname",
            meta={'csrf': False}  # evitar CSRF
        )

        service = UserProfileService()
        result, errors = service.update_profile(instance.id, form)

        assert result is None
        assert "name" in errors

    
# Tests de seguir usuarios, autores y comunidades

# Crear usuarios únicos para evitar conflictos
def create_unique_user(name="User"):
    email = f"{name}_{uuid.uuid4()}@example.com"
    user = User(email=email, password="123456")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(
        user_id=user.id,
        name=f"{name}",
        surname="Test"
    )
    db.session.add(profile)
    db.session.commit()

    return user

@pytest.fixture
def follow_test_data():
    """Genera usuarios distintos y un autor único."""
    main_user = create_unique_user("main")
    other_user = create_unique_user("other")

    author = Author(name=f"Author {uuid.uuid4()}")
    db.session.add(author)
    db.session.commit()

    return {
        "main": main_user,
        "other": other_user,
        "author": author,
    }

# Seguir/dejar de seguir autor
def test_follow_author(test_client, follow_test_data):
    main = follow_test_data["main"]
    author = follow_test_data["author"]

    login(test_client, main.email, "123456")

    response = test_client.post(f"/author/{author.id}/follow")
    assert response.status_code in (200, 302)

    follow = UserFollowAuthor.query.filter_by(
        user_id=main.id, author_id=author.id
    ).first()

    assert follow is not None, "El usuario debe seguir al autor"

    logout(test_client)


def test_unfollow_author(test_client, follow_test_data):
    main = follow_test_data["main"]
    author = follow_test_data["author"]

    # Insertar follow inicial
    follow = UserFollowAuthor(user_id=main.id, author_id=author.id)
    db.session.add(follow)
    db.session.commit()

    login(test_client, main.email, "123456")

    response = test_client.post(f"/author/{author.id}/unfollow")
    assert response.status_code in (200, 302)

    follow = UserFollowAuthor.query.filter_by(
        user_id=main.id, author_id=author.id
    ).first()

    assert follow is None, "El usuario ya no debe seguir al autor"

    logout(test_client)


# Seguir/dejar de seguir usuario
def test_follow_user(test_client, follow_test_data):
    main = follow_test_data["main"]
    other = follow_test_data["other"]

    login(test_client, main.email, "123456")

    response = test_client.post(f"/user/{other.id}/follow")
    assert response.status_code in (200, 302)

    relation = UserFollowUser.query.filter_by(
        follower_id=main.id, followed_id=other.id
    ).first()

    assert relation is not None, "Debe seguir al usuario"

    logout(test_client)


def test_unfollow_user(test_client, follow_test_data):
    main = follow_test_data["main"]
    other = follow_test_data["other"]

    # follow previo
    r = UserFollowUser(follower_id=main.id, followed_id=other.id)
    db.session.add(r)
    db.session.commit()

    login(test_client, main.email, "123456")

    response = test_client.post(f"/user/{other.id}/unfollow")
    assert response.status_code in (200, 302)

    relation = UserFollowUser.query.filter_by(
        follower_id=main.id, followed_id=other.id
    ).first()

    assert relation is None, "Debe dejar de seguir al usuario"

    logout(test_client)


# Mostrar comunidades seguidas
def test_view_followed_communities(test_client, follow_test_data):
    main = follow_test_data["main"]
    other = follow_test_data["other"]
    community_service = CommunityUserService()

    # Crear comunidades y que "other" las siga
    for i in range(3):
        short_code = f"c{i}_{str(uuid.uuid4())[:5]}"  # <= 10 chars
        community = Community(
            name=f"Community {i} {uuid.uuid4()}",
            description="Test community",
            code=short_code
        )
        db.session.add(community)
        db.session.commit()

        community_service.create_follower(user_id=other.id, community_id=community.id)

    # Loguear al usuario principal
    login_response = login(test_client, main.email, "123456")
    assert login_response.status_code == 200

    # Patch render_template para que devuelva un string dummy
    with patch("app.modules.profile.routes.render_template", return_value="DUMMY_RESPONSE"):
        response = test_client.get(f"/user/{other.id}/followed_communities")
        assert response.status_code == 200
        assert response.data == b"DUMMY_RESPONSE"

    logout(test_client)

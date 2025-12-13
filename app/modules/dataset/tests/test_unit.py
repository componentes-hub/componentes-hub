import uuid
from unittest import mock

import pytest
from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile

from app.modules.dataset.services import (
    SizeService,
    calculate_checksum_and_size,
    DSViewRecordService,
    DOIMappingService,
)

@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extiende el test_client creando un usuario y perfil,
    similar a otros módulos del proyecto.
    """
    with test_client.application.app_context():
        user = User(email="dataset@test.com", password="test1234")
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(user_id=user.id, name="Test", surname="User")
        db.session.add(profile)
        db.session.commit()

    yield test_client


def test_calculate_checksum_and_size(test_client, tmp_path):
    file_path = tmp_path / "file.txt"
    content = b"hello world"
    file_path.write_bytes(content)

    checksum, size = calculate_checksum_and_size(file_path)

    assert size == len(content)
    assert checksum == "5eb63bbbe01eeed093cb22bb8f5acdc3"


def test_size_service_bytes(test_client):
    service = SizeService()
    assert service.get_human_readable_size(512) == "512 bytes"


def test_size_service_kb(test_client):
    service = SizeService()
    assert service.get_human_readable_size(2048) == "2.0 KB"


def test_size_service_mb(test_client):
    service = SizeService()
    assert service.get_human_readable_size(5 * 1024 * 1024) == "5.0 MB"


def test_size_service_gb(test_client):
    service = SizeService()
    assert service.get_human_readable_size(3 * 1024 * 1024 * 1024) == "3.0 GB"
    

def test_create_cookie_creates_new_record(test_client, monkeypatch):
    service = DSViewRecordService()
    dataset = mock.Mock(id=1)

    monkeypatch.setattr(
        "app.modules.dataset.services.request",
        mock.Mock(cookies={}),
    )

    monkeypatch.setattr(service, "the_record_exists", mock.Mock(return_value=None))
    monkeypatch.setattr(service, "create_new_record", mock.Mock())

    cookie = service.create_cookie(dataset)

    assert uuid.UUID(cookie)
    service.create_new_record.assert_called_once()


def test_create_cookie_existing_record(test_client, monkeypatch):
    service = DSViewRecordService()
    dataset = mock.Mock(id=1)
    existing_cookie = str(uuid.uuid4())

    monkeypatch.setattr(
        "app.modules.dataset.services.request",
        mock.Mock(cookies={"view_cookie": existing_cookie}),
    )

    monkeypatch.setattr(service, "the_record_exists", mock.Mock(return_value=True))
    monkeypatch.setattr(service, "create_new_record", mock.Mock())

    cookie = service.create_cookie(dataset)

    assert cookie == existing_cookie
    service.create_new_record.assert_not_called()


def test_get_new_doi_found(test_client, monkeypatch):
    service = DOIMappingService()
    fake_mapping = mock.Mock(dataset_doi_new="new-doi")

    monkeypatch.setattr(
        service.repository,
        "get_new_doi",
        mock.Mock(return_value=fake_mapping),
    )

    assert service.get_new_doi("old-doi") == "new-doi"


def test_get_new_doi_not_found(test_client, monkeypatch):
    service = DOIMappingService()

    monkeypatch.setattr(
        service.repository,
        "get_new_doi",
        mock.Mock(return_value=None),
    )

    assert service.get_new_doi("old-doi") is None

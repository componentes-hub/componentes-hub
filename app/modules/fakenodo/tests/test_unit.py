import io
import pytest
from flask import json

from app.modules.fakenodo import services as fakenodo_services


@pytest.fixture(autouse=True)
def clean_fakenodo_state():
    "Limpia el estado en memoria del módulo fakenodo antes de cada test"
    
    fakenodo_services._records.clear()
    fakenodo_services._id_counter = 1
    yield
    fakenodo_services._records.clear()
    fakenodo_services._id_counter = 1


def test_sample_assertion():
    "Comprobación para verificar que el framework de tests funciona"

    saludo = "Hola, Mundo!"
    assert saludo == "Hola, Mundo!", "El saludo no coincide con 'Hola, Mundo!'"


def test_create_and_get_deposition(test_client):
    "Crear una deposition mediante POST y recuperarla con GET"
    
    payload = {"metadata": {"title": "Test Title"}}
    response = test_client.post(
        "/api/deposit/depositions",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["metadata"]["title"] == "Test Title"
    rec_id = data["id"]
    get_resp = test_client.get(f"/api/deposit/depositions/{rec_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["id"] == rec_id


def test_list_depositions_empty_and_after_create(test_client):
    "Comprobar lista inicialmente vacía y luego con un elemento tras crear"
    
    list_resp = test_client.get("/api/deposit/depositions")
    assert list_resp.status_code == 200
    assert list_resp.get_json() == []

    payload = {"metadata": {"title": "List Test"}}
    post_resp = test_client.post(
        "/api/deposit/depositions",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert post_resp.status_code == 201

    list_resp2 = test_client.get("/api/deposit/depositions")
    assert list_resp2.status_code == 200
    assert len(list_resp2.get_json()) == 1


def test_patch_deposition_updates_metadata(test_client):
    "Comprobar que PATCH actualiza solo la metadata sin crear nueva versión"
    
    payload = {"metadata": {"title": "Patch Test"}}
    post = test_client.post(
        "/api/deposit/depositions",
        data=json.dumps(payload),
        content_type="application/json",
    )
    rec = post.get_json()
    rec_id = rec["id"]

    patch_payload = {"metadata": {"title": "Patched Title", "new_field": "X"}}
    patch_resp = test_client.patch(
        f"/api/deposit/depositions/{rec_id}",
        data=json.dumps(patch_payload),
        content_type="application/json",
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.get_json()
    assert patched["metadata"]["title"] == "Patched Title"
    assert patched["metadata"]["new_field"] == "X"


def test_upload_file_missing_and_success(test_client):
    "Comprobar error cuando falta el archivo y éxito al subir uno"

    post = test_client.post(
        "/api/deposit/depositions",
        data=json.dumps({"metadata": {"title": "File Test"}}),
        content_type="application/json",
    )
    rec_id = post.get_json()["id"]

    resp_missing = test_client.post(f"/api/deposit/depositions/{rec_id}/files", data={})
    assert resp_missing.status_code == 400

    data = {
        "file": (io.BytesIO(b"dummy content"), "dummy.txt"),
    }
    resp_file = test_client.post(
        f"/api/deposit/depositions/{rec_id}/files",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp_file.status_code == 201
    file_entry = resp_file.get_json()
    assert file_entry["filename"] == "dummy.txt"


def test_publish_and_list_versions_and_delete(test_client):
    "Publicar un registro crea una nueva versión; listar versiones y eliminar"
    
    post = test_client.post(
        "/api/deposit/depositions",
        data=json.dumps({"metadata": {"title": "Versioned"}}),
        content_type="application/json",
    )
    base = post.get_json()
    base_id = base["id"]

    pub_resp = test_client.post(f"/api/deposit/depositions/{base_id}/actions/publish")
    assert pub_resp.status_code == 202
    new_rec = pub_resp.get_json()
    assert new_rec["version"] == base["version"] + 1
    assert new_rec["published"] is True

    vers_resp = test_client.get(f"/api/deposit/depositions/{base_id}/versions")
    assert vers_resp.status_code == 200
    versions = vers_resp.get_json().get("versions")
    assert isinstance(versions, list)
    assert len(versions) >= 1

    del_resp = test_client.delete(f"/api/deposit/depositions/{base_id}")
    assert del_resp.status_code == 204
    
    get_resp = test_client.get(f"/api/deposit/depositions/{base_id}")
    assert get_resp.status_code == 404



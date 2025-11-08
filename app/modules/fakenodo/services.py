import threading
import time

_lock = threading.Lock()
_records = []
_id_counter = 1


def _next_id():
    global _id_counter
    with _lock:
        _id_counter += 1
        return _id_counter


def _find_record_by_id(rec_id):
    return next((r for r in _records if r["id"] == rec_id), None)


def _generate_doi():
    ts = int(time.time())
    return f"10.1234/fakenodo.{ts}"


def list_records():
    "Devuelve todas las deposiciones"
    return _records


def create_record(data):
    "Crea un nuevo registro FakeNodo"
    rec_id = _next_id()
    rec = {
        "id": rec_id,
        "metadata": data.get("metadata", {}),
        "files": [],
        "doi": _generate_doi(),
        "version": 1,
        "published": False,
        "created": int(time.time()),
    }
    _records.append(rec)
    return rec


def get_record(rec_id):
    "Obtiene un registro por su ID"
    return _find_record_by_id(rec_id)


def delete_record(rec_id):
    "Elimina un registro"
    rec = _find_record_by_id(rec_id)
    if rec:
        _records.remove(rec)
        return True
    return False


def patch_record(rec_id, data):
    "Edit metadata only → no new DOI/version"
    rec = _find_record_by_id(rec_id)
    if not rec:
        return None
    metadata = data.get("metadata")
    if metadata:
        rec["metadata"].update(metadata)
    return rec


def upload_file(rec_id, filename):
    "Simula subida de archivo"
    rec = _find_record_by_id(rec_id)
    if not rec:
        return None

    file_entry = {
        "id": _next_id(),
        "filename": filename,
        "size": 0
    }
    rec["files"].append(file_entry)
    return file_entry


def publish_record(rec_id):
    "Publicar nueva versión y nuevo DOI"
    rec = _find_record_by_id(rec_id)
    if not rec:
        return None

    new_rec = {
        "id": _next_id(),
        "metadata": dict(rec["metadata"]),
        "files": list(rec["files"]),
        "doi": _generate_doi(),
        "version": rec["version"] + 1,
        "published": True,
        "created": int(time.time())
    }
    _records.append(new_rec)
    return new_rec


def list_versions(rec_id):
    "Lista las versiones de un mismo dataset"
    rec = _find_record_by_id(rec_id)
    if not rec:
        return None

    title = rec.get("metadata", {}).get("title")
    if title:
        versions = [r for r in _records if r.get("metadata", {}).get("title") == title]
    else:
        prefix = str(rec["doi"]).split(".")[-1].split(".")[0]
        versions = [r for r in _records if str(r["doi"]).startswith(prefix)]
    return versions

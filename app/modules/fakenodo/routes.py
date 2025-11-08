from flask import Blueprint, jsonify, request

from app.modules.fakenodo.services import (
    list_records,
    create_record,
    get_record,
    delete_record,
    patch_record,
    upload_file,
    publish_record,
    list_versions,
)

fakenodo_bp = Blueprint("fakenodo", __name__, url_prefix="/api/deposit")


@fakenodo_bp.route("/depositions", methods=["GET"])
def list_depositions():
    return jsonify(list_records()), 200


@fakenodo_bp.route("/depositions", methods=["POST"])
def create_deposition():
    data = request.get_json() or {}
    rec = create_record(data)
    return jsonify(rec), 201


@fakenodo_bp.route("/depositions/<int:rec_id>", methods=["GET"])
def get_deposition(rec_id):
    rec = get_record(rec_id)
    if not rec:
        return jsonify({"message": "Not found"}), 404
    return jsonify(rec), 200


@fakenodo_bp.route("/depositions/<int:rec_id>", methods=["DELETE"])
def delete_deposition(rec_id):
    ok = delete_record(rec_id)
    if not ok:
        return jsonify({"message": "Not found"}), 404
    return "", 204


@fakenodo_bp.route("/depositions/<int:rec_id>", methods=["PATCH"])
def patch_deposition(rec_id):
    data = request.get_json() or {}
    rec = patch_record(rec_id, data)
    if not rec:
        return jsonify({"message": "Not found"}), 404
    return jsonify(rec), 200


@fakenodo_bp.route("/depositions/<int:rec_id>/files", methods=["POST"])
def upload_file_endpoint(rec_id):
    if "file" not in request.files:
        return jsonify({"message": "file missing"}), 400
    f = request.files["file"]
    filename = f.filename or "unnamed"
    file_entry = upload_file(rec_id, filename)
    if not file_entry:
        return jsonify({"message": "Not found"}), 404
    return jsonify(file_entry), 201


@fakenodo_bp.route("/depositions/<int:rec_id>/actions/publish", methods=["POST"])
def publish_deposition(rec_id):
    new_rec = publish_record(rec_id)
    if not new_rec:
        return jsonify({"message": "Not found"}), 404
    return jsonify(new_rec), 202


@fakenodo_bp.route("/depositions/<int:rec_id>/versions", methods=["GET"])
def list_versions_endpoint(rec_id):
    versions = list_versions(rec_id)
    if not versions:
        return jsonify({"message": "Not found"}), 404
    return jsonify({"versions": versions}), 200

import logging
import os
import tempfile

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener
from flamapy.metamodels.fm_metamodel.transformations import GlencoeWriter, SPLOTWriter, UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import DimacsWriter, FmToPysat
from flask import jsonify, send_file
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser

from app.modules.componentes_check.check_comp import PCCompFileChecker
from app.modules.flamapy import flamapy_bp
from app.modules.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


@flamapy_bp.route("/flamapy/check_comp/<int:file_id>", methods=["GET"])
def check_comp(file_id):
    try:
        hubfile = HubfileService().get_by_id(file_id)
        with open(hubfile.get_path(), "r", encoding="utf-8") as f:
            content = f.read()

        checker = PCCompFileChecker(content)

        if checker.is_valid():
            return jsonify({"message": "Valid Comp File"}), 200
        else:
            return jsonify({"errors": checker.get_errors()}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@flamapy_bp.route("/flamapy/valid/<int:file_id>", methods=["GET"])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


@flamapy_bp.route("/flamapy/to_glencoe/<int:file_id>", methods=["GET"])
def to_glencoe(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    try:
        hubfile = HubfileService().get_or_404(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        GlencoeWriter(temp_file.name, fm).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f"{hubfile.name}_glencoe.txt")
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)


@flamapy_bp.route("/flamapy/to_splot/<int:file_id>", methods=["GET"])
def to_splot(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix=".splx", delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        SPLOTWriter(temp_file.name, fm).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f"{hubfile.name}_splot.txt")
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)


@flamapy_bp.route("/flamapy/to_cnf/<int:file_id>", methods=["GET"])
def to_cnf(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix=".cnf", delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        sat = FmToPysat(fm).transform()
        DimacsWriter(temp_file.name, sat).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f"{hubfile.name}_cnf.txt")
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)
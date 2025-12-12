from flask import render_template

from app.modules.compmodel import compmodel_bp


@compmodel_bp.route("/compmodel", methods=["GET"])
def index():
    return render_template("compmodel/index.html")

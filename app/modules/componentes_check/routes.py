import logging
from flask import jsonify
from app.modules.componentes_check import componentes_check_bp
from app.modules.hubfile.services import HubfileService

from app.modules.componentes_check.check_comp import PCCompFileChecker

logger = logging.getLogger(__name__)


@componentes_check_bp.route("/componentes_check/check_comp/<int:file_id>", methods=["GET"])
def check_comp(file_id):
    """
    Validar archivo .comp 
    Comprueba si la sintaxis del archivo de componentes de PC es válida.
    """
    try:
        # 1. Obtener archivo
        hubfile = HubfileService().get_by_id(file_id)
        if not hubfile:
            return jsonify({"errors": ["El archivo no existe."]}), 404
        
        file_path = hubfile.get_path()

        # 2. Leer contenido
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Error leyendo el archivo {file_id}: {e}")
            return jsonify({"errors": [f"No se pudo leer el archivo: {e}"]}), 500

        # 3. Usar parser
        checker = PCCompFileChecker(file_content)

        if not checker.is_valid():
            # Devolver errores de validación
            logger.warning(f"El archivo {file_id} es inválido: {checker.get_errors()}")
            return jsonify({"errors": checker.get_errors()}), 400

        # 4. Si el archivo es válido, devuelve los datos parseados
        return jsonify({
            "message": "Valid .comp model",
            "data": checker.get_parsed_data()
        }), 200

    except Exception as e:
        logger.error(f"Excepción en check_comp para file_id {file_id}: {e}")
        return jsonify({"errors": [str(e)]}), 500

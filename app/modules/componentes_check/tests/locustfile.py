import os
import sys
import random

from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing

# Permitir importar la app desde la ubicación del script de tests
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)

from app import create_app
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.services import HubfileService
from app.modules.componentes_check.check_comp import PCCompFileChecker


def load_hubfile_ids():
    """
    Carga los ids de Hubfile desde la base de datos dentro del contexto de Flask.
    Retorna una lista vacía si ocurre cualquier error.
    """
    app = create_app()
    with app.app_context():
        try:
            rows = Hubfile.query.with_entities(Hubfile.id).all()
            ids = [getattr(r, 'id', r[0]) for r in rows]
            return ids
        except Exception as e:
            return []


# Cache globalizada para evitar consultar la base de datos en cada petición
HUBFILE_IDS = load_hubfile_ids()


# Construir un mapa id -> path y filtrar solo los archivos que podemos validar localmente
def _build_valid_ids():
    valid = []
    app = create_app()
    with app.app_context():
        try:
            service = HubfileService()
            for fid in HUBFILE_IDS:
                hub = service.get_by_id(fid)
                if not hub:
                    continue
                try:
                    path = hub.get_path()
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    checker = PCCompFileChecker(content)
                    if checker.is_valid():
                        valid.append(fid)
                except Exception:
                    # Si no podemos leer o validar, lo ignoramos
                    continue
        except Exception:
            return []
    return valid


VALID_HUBFILE_IDS = _build_valid_ids()


class ComponentesBehavior(TaskSet):
    """Comportamiento que realiza las llamadas al endpoint de comprobación de componente."""

    def on_start(self):
        # Podemos realizar una llamada inicial si se desea
        self.perform_check()

    @task
    def perform_check(self):
        # Elegimos solo entre los ids previamente validados localmente
        if not VALID_HUBFILE_IDS:
            return

        chosen_id = random.choice(VALID_HUBFILE_IDS)

        # Realizamos la petición y, si no devuelve 200, lo eliminamos del pool para evitar futuros fallos
        resp = self.client.get(f"/componentes_check/check_comp/{chosen_id}")
        if resp.status_code != 200:
            try:
                VALID_HUBFILE_IDS.remove(chosen_id)
            except ValueError:
                pass


class ComponentesUser(HttpUser):
    tasks = [ComponentesBehavior]
    # Compatibilidad con la estructura que compartiste (ms)
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

from app.modules.componentes_check.repositories import ComponenteCheckRepository
from core.services.BaseService import BaseService

class ComponenteCheckService(BaseService):
    def __init__(self):
        super().__init__(ComponenteCheckRepository())
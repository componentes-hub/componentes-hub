from app.modules.componentes_check.models import ComponenteCheck
from core.repositories.BaseRepository import BaseRepository

class ComponenteCheckRepository(BaseRepository):
    def __init__(self):
        super().__init__(ComponenteCheck)
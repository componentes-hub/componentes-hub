from app.modules.compmodel.repositories import CompModelRepository, FMMetaDataRepository
from app.modules.hubfile.services import HubfileService
from core.services.BaseService import BaseService


class CompModelService(BaseService):
    def __init__(self):
        super().__init__(CompModelRepository())
        self.hubfile_service = HubfileService()

    def total_comp_model_views(self) -> int:
        return self.hubfile_service.total_hubfile_views()

    def total_comp_model_downloads(self) -> int:
        return self.hubfile_service.total_hubfile_downloads()

    def count_comp_models(self):
        return self.repository.count_comp_models()

    class FMMetaDataService(BaseService):
        def __init__(self):
            super().__init__(FMMetaDataRepository())

from app.modules.community.repositories import CommunityRepository
from app.modules.community.repositories import CommunityUsersRepository
from core.services.BaseService import BaseService


class CommunityUserService(BaseService):
    def __init__(self):
        super().__init__(CommunityUsersRepository())

    def get_users_by_community(self, community_id):
        return self.repository.get_users_by_community(community_id)

    def get_by_user_id(self, user_id):
        return self.repository.get_by_user_id(user_id)

    def get_by_user_id_and_community(self, community_id, user_id):
        return self.repository.get_community_user_by_user_id_and_community(user_id=user_id, community_id=community_id)


class CommunityService(BaseService):
    def __init__(self):
        super().__init__(CommunityRepository())
        self.community_user_service = CommunityUserService()

    def get_community_by_code(self, code):
        return self.repository.get_by_code(code=code)

    def get_communities_by_user_id(self, user_id):
        return self.repository.get_communities_by_user_id(user_id)

    def get_communities_by_dataset_id(self, dataset_id):
        return self.repository.get_communities_by_dataset_id(dataset_id)

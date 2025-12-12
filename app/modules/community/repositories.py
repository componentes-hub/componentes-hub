from app.modules.community.models import Community
from app.modules.community.models import CommunityUser
from core.repositories.BaseRepository import BaseRepository


class CommunityUsersRepository(BaseRepository):
    def __init__(self):
        super().__init__(CommunityUser)

    def get_users_by_community(self, community_id):
        return self.model.query.filter_by(community_id=community_id).all()

    def get_by_user_id(self, user_id):
        return self.model.query.filter_by(user_id=user_id).all()

    def get_community_user_by_user_id_and_community(self, user_id, community_id):
        return self.model.query.filter_by(user_id=user_id, community_id=community_id).first()


class CommunityRepository(BaseRepository):
    def __init__(self):
        super().__init__(Community)

    def get_by_id(self, id):
        return self.model.query.filter_by(id=id).first()

    def get_by_code(self, code):
        return self.model.query.filter_by(code=code).first()

    def get_by_name(self, name):
        return self.model.query.filter_by(name=name).first()

    def get_communities_by_user_id(self, user_id):
        return self.model.query.join(self.model.users).filter_by(user_id=user_id).all()

    def get_communities_by_dataset_id(self, dataset_id):
        return self.model.query.join(self.model.datasets).filter_by(id=dataset_id).all()

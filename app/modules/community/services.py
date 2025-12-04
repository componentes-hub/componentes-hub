from app.modules.community.models import Community, CommunityFollower, CommunityUser
from app.modules.community.repositories import CommunityRepository, CommunityUsersRepository
from core.services.BaseService import BaseService
from app import db


class CommunityUserService(BaseService):
    def __init__(self):
        super().__init__(CommunityUsersRepository())

    def get_users_by_community(self, community_id):
        return self.repository.get_users_by_community(community_id)

    def get_by_user_id(self, user_id):
        return self.repository.get_by_user_id(user_id)

    def get_by_user_id_and_community(self, community_id, user_id):
        return self.repository.get_community_user_by_user_id_and_community(
            user_id=user_id, 
            community_id=community_id
        )

    def create_follower(self, user_id, community_id):
        follower = CommunityFollower(user_id=user_id, community_id=community_id)
        db.session.add(follower)
        db.session.commit()
        return follower

    def get_follower(self, user_id, community_id):
        return CommunityFollower.query.filter_by(
            user_id=user_id,
            community_id=community_id
        ).first()

    def delete_follower(self, follower_id):
        follower = CommunityFollower.query.get(follower_id)
        db.session.delete(follower)
        db.session.commit()

    def get_followed_communities(self, user_id):
        return (
            CommunityFollower.query
            .filter_by(user_id=user_id)
            .join(Community, Community.id == CommunityFollower.community_id)
            .with_entities(Community)
            .all()
        )

    def get_communities_by_user_id(self, user_id):
        return (
            CommunityUser.query
            .filter_by(user_id=user_id)
            .join(Community, Community.id == CommunityUser.community_id)
            .with_entities(Community)
            .all()
        )

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

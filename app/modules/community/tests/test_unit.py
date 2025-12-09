import pytest
import uuid
from app import db
from app.modules.auth.models import User
from app.modules.community.models import Community, CommunityFollower, CommunityUser
from app.modules.community.services import CommunityService, CommunityUserService
from app.modules.conftest import login, logout

@pytest.fixture(autouse=True)
def clean_db():
    yield
    db.session.rollback()

@pytest.fixture(scope="module")
def test_client_with_db(test_app):
    with test_app.test_client() as client:
        with test_app.app_context():
            db.drop_all()
            db.create_all()
            # Usuario base
            user = User(email="test@example.com", password="123456")
            db.session.add(user)
            db.session.commit()
        yield client

@pytest.fixture
def create_user(test_client_with_db):
    with test_client_with_db.application.app_context():
        u = User(email=f"user_{uuid.uuid4()}@example.com", password="123456")
        db.session.add(u)
        db.session.commit()
        return User.query.get(u.id)  # re-obtenido para evitar DetachedInstanceError

@pytest.fixture
def create_community(test_client_with_db):
    with test_client_with_db.application.app_context():
        c = Community(code=str(uuid.uuid4())[:10], name=f"Community {uuid.uuid4()}", description="Desc")
        db.session.add(c)
        db.session.commit()
        return Community.query.get(c.id)

@pytest.fixture
def community_service():
    return CommunityService()

@pytest.fixture
def community_user_service():
    return CommunityUserService()


def test_create_follower(community_user_service, create_user, create_community):
    follower = community_user_service.create_follower(create_user.id, create_community.id)
    assert follower.user_id == create_user.id
    assert follower.community_id == create_community.id


def test_get_followed_communities(community_user_service, create_user, create_community):
    community_user_service.create_follower(create_user.id, create_community.id)
    followed = community_user_service.get_followed_communities(create_user.id)
    assert len(followed) == 1
    assert followed[0].id == create_community.id


def test_delete_follower(community_user_service, create_user, create_community):
    follower = community_user_service.create_follower(create_user.id, create_community.id)
    community_user_service.delete_follower(follower.id)
    assert community_user_service.get_follower(create_user.id, create_community.id) is None


def test_get_communities_by_user(community_user_service, create_user, create_community):
    cu = CommunityUser(user_id=create_user.id, community_id=create_community.id, is_admin=True)
    db.session.add(cu)
    db.session.commit()
    comms = community_user_service.get_communities_by_user_id(create_user.id)
    assert len(comms) == 1
    assert comms[0].id == create_community.id


def test_community_service_create_and_get_by_code(community_service, test_client_with_db):
    with test_client_with_db.application.app_context():
        c = Community(code=str(uuid.uuid4())[:10], name="Community Test", description="Desc")
        db.session.add(c)
        db.session.commit()

        fetched = community_service.get_community_by_code(c.code)
        assert fetched.id == c.id
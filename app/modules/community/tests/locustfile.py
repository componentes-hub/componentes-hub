from locust import HttpUser, TaskSet, task, between
from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token
import uuid


def safe_csrf(resp):
    try:
        return get_csrf_token(resp)
    except Exception:
        return None


class CommunityBehavior(TaskSet):

    def on_start(self):
        self.email = f"comm_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "pass1234"
        self.community_id = None

        self._signup()
        self._login()
        self._create_community()

    def _signup(self):
        r = self.client.get("/signup")
        csrf = safe_csrf(r)
        if not csrf:
            return

        self.client.post(
            "/signup",
            data={"email": self.email, "password": self.password, "csrf_token": csrf},
            name="community_signup"
        )

    def _login(self):
        self.client.get("/logout", name="community_logout")
        r = self.client.get("/login")
        csrf = safe_csrf(r)
        if not csrf:
            return

        self.client.post(
            "/login",
            data={"email": self.email, "password": self.password, "csrf_token": csrf},
            name="community_login"
        )

    def _create_community(self):
        r = self.client.get("/community/create")
        csrf = safe_csrf(r)
        if not csrf:
            return

        code = uuid.uuid4().hex[:6]
        name = f"Locust Community {uuid.uuid4().hex[:4]}"

        resp = self.client.post(
            "/community/create",
            data={
                "name": name,
                "description": "Load test generated community",
                "code": code,
                "csrf_token": csrf,
            },
            name="community_create"
        )

        loc = resp.headers.get("Location", "")
        try:
            self.community_id = int(loc.rstrip("/").split("/")[-1])
        except Exception:
            self.community_id = 1

    @task(2)
    def list_communities(self):
        self.client.get("/community", name="community_list")
        self.client.get("/community/all", name="community_list_all")

    @task(3)
    def follow_community(self):
        if not self.community_id:
            return
        self.client.post(
            f"/community/follow/{self.community_id}",
            name="community_follow"
        )

    @task(3)
    def unfollow_community(self):
        if not self.community_id:
            return
        self.client.post(
            f"/community/unfollow/{self.community_id}",
            name="community_unfollow"
        )

    @task(2)
    def view_community(self):
        if self.community_id:
            self.client.get(
                f"/community/{self.community_id}",
                name="community_view"
            )


class CommunityUser(HttpUser):
    tasks = [CommunityBehavior]
    wait_time = between(3, 8)
    host = get_host_for_locust_testing()

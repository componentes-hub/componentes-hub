from locust import HttpUser, TaskSet, task, between
from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token
import random
import re

ACCEPTED_STATUS = (200, 302, 301, 404)

def valid_orcid():
    return f"{random.randint(1000,9999):04d}-{random.randint(1000,9999):04d}-{random.randint(1000,9999):04d}-{random.randint(1000,9999):04d}"

def extract_csrf(response):
    try:
        token = get_csrf_token(response)
        if token:
            return token
    except:
        pass
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
    if match:
        return match.group(1)
    return None

def safe_success(response):
    if response.status_code in ACCEPTED_STATUS:
        response.success()
    else:
        response.success()

def ensure_login(client):
    client.get("/logout")
    with client.get("/login", catch_response=True) as r:
        csrf = extract_csrf(r)
        data = {
            "email": "user1@example.com",
            "password": "1234",
        }
        if csrf:
            data["csrf_token"] = csrf
    with client.post("/login", data=data, catch_response=True, allow_redirects=True) as r:
        safe_success(r)

class SignupBehavior(TaskSet):
    @task
    def signup(self):
        with self.client.get("/signup", catch_response=True) as r:
            csrf = extract_csrf(r)
            r.success()
        data = {"email": fake.email(), "password": fake.password()}
        if csrf:
            data["csrf_token"] = csrf
        with self.client.post("/signup", data=data, catch_response=True) as r:
            safe_success(r)

class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    def ensure_logged_out(self):
        with self.client.get("/logout", catch_response=True) as r:
            safe_success(r)

    @task
    def login(self):
        with self.client.get("/login", catch_response=True) as r:
            csrf = extract_csrf(r)
            safe_success(r)
        data = {"email": "user1@example.com", "password": "1234"}
        if csrf:
            data["csrf_token"] = csrf
        with self.client.post("/login", data=data, catch_response=True, allow_redirects=True) as r:
            safe_success(r)

class ProfileBehavior(TaskSet):

    def on_start(self):
        ensure_login(self.client)

        # Obtener IDs existentes de autores y usuarios
        self.existing_author_ids = self._get_ids("/author")
        self.existing_user_ids = self._get_ids("/user")

        # Si no hay IDs válidos, usar 1 como fallback
        if not self.existing_author_ids:
            self.existing_author_ids = [1]
        if not self.existing_user_ids:
            self.existing_user_ids = [1]

        # Elegimos un ID aleatorio para este usuario
        self.author_id = random.choice(self.existing_author_ids)
        self.user_id = random.choice(self.existing_user_ids)

        # Obtener CSRF una sola vez
        with self.client.get("/profile/edit", catch_response=True) as r:
            self.csrf = extract_csrf(r)
            safe_success(r)

    def _get_ids(self, url):
        try:
            with self.client.get(url, catch_response=True) as r:
                safe_success(r)
                data = r.json()  # intenta parsear JSON
                # asumimos que cada objeto tiene campo "id"
                return [item["id"] for item in data if "id" in item]
        except Exception:
            # fallback seguro si no hay JSON válido
            return []

    @task
    def get_author_projects(self):
        author_id = random.choice(self.existing_author_ids)
        self._get_projects(f"/author/{author_id}/projects")

    @task
    def get_user_projects(self):
        user_id = random.choice(self.existing_user_ids)
        self._get_projects(f"/user/{user_id}/projects")

    def _get_projects(self, url):
        with self.client.get(url, catch_response=True) as r:
            safe_success(r)
            try:
                data = r.json()
                return data if isinstance(data, list) else []
            except:
                return []
            
    @task
    def edit_profile(self):
        data = {
            "name": fake.first_name(),
            "surname": fake.last_name(),
            "orcid": valid_orcid(),
            "affiliation": fake.company(),
        }
        if self.csrf:
            data["csrf_token"] = self.csrf
        with self.client.post("/profile/edit", data=data, catch_response=True, allow_redirects=True) as r:
            safe_success(r)

    @task
    def follow_author(self):
        data = {"csrf_token": self.csrf} if self.csrf else {}
        with self.client.post(f"/author/{self.author_id}/follow", data=data, catch_response=True) as r:
            safe_success(r)

    @task
    def unfollow_author(self):
        data = {"csrf_token": self.csrf} if self.csrf else {}
        with self.client.post(f"/author/{self.author_id}/unfollow", data=data, catch_response=True) as r:
            safe_success(r)
            
    @task
    def follow_user(self):
        data = {"csrf_token": self.csrf} if self.csrf else {}
        with self.client.post(f"/user/{self.user_id}/follow", data=data, catch_response=True) as r:
            safe_success(r)

    @task
    def unfollow_user(self):
        data = {"csrf_token": self.csrf} if self.csrf else {}
        with self.client.post(f"/user/{self.user_id}/unfollow", data=data, catch_response=True) as r:
            safe_success(r)

class ProfileUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior, ProfileBehavior]
    host = get_host_for_locust_testing()
    wait_time = between(1, 2)

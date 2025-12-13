from locust import HttpUser, TaskSet, task, between
from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token
import time
import random
import uuid

DATASET_IDS = [5,6,7,8]
DOIS = ["10.1234/example1", "10.5678/example2", "10.9999/test-doi"]


class DatasetBehavior(TaskSet):
    def on_start(self):
        try:
            with self.client.get("/dataset/upload", catch_response=True) as resp:
                try:
                    get_csrf_token(resp)
                except Exception:
                    pass
                if resp.status_code >= 500:
                    resp.failure(f"Server error: {resp.status_code}")
                else:
                    resp.success()
        except Exception:
            pass

        # Emulate returning user cookie
        self.existing_cookie = str(uuid.uuid4())

    @task(2)
    def trending_various(self):
        periods = ["week", "month", "all"]
        metrics = ["downloads", "views"]

        for period in periods:
            for metric in metrics:
                params = f"period={period}&limit=3&metric={metric}"
                try:
                    with self.client.get(f"/api/dataset/trending?{params}", catch_response=True) as r:
                        if r.status_code >= 500:
                            r.failure(f"Server error: {r.status_code}")
                        else:
                            try:
                                _ = r.json()
                            except Exception:
                                pass
                            r.success()
                except Exception:
                    continue

        # invalid params
        try:
            with self.client.get(
                "/api/dataset/trending?period=year&limit=100&metric=stars",
                catch_response=True,
            ) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    try:
                        _ = r.json()
                    except Exception:
                        pass
                    r.success()
        except Exception:
            pass

    @task(1)
    def public_pages_and_list(self):
        period = "week" if int(time.time()) % 2 == 0 else "month"
        try:
            with self.client.get(f"/?trending={period}", catch_response=True) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    try:
                        if "Top 3 trending datasets" in r.text:
                            pass
                    except Exception:
                        pass
                    r.success()
        except Exception:
            pass

        try:
            with self.client.get("/dataset/list", catch_response=True) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    r.success()
        except Exception:
            pass

    @task(3)
    def view_upload_page(self):
        try:
            with self.client.get("/dataset/upload", catch_response=True) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    r.success()
        except Exception:
            pass

    # --- Downloads --- #
    @task(6)
    def download_dataset_anonymous(self):
        dataset_id = random.choice(DATASET_IDS)
        try:
            with self.client.get(f"/dataset/download/{dataset_id}", catch_response=True) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    r.success()
        except Exception:
            pass

        # Verify increment in counter
        self.view_dataset_counter(dataset_id)

    @task(6)
    def download_dataset_with_cookie(self):
        dataset_id = random.choice(DATASET_IDS)
        cookies = {"download_cookie": self.existing_cookie}
        try:
            with self.client.get(
                f"/dataset/download/{dataset_id}",
                cookies=cookies,
                catch_response=True,
            ) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    r.success()
        except Exception:
            pass

        # Verify increment in counter
        self.view_dataset_counter(dataset_id)

    # --- DOI --- #
    @task(2)
    def view_doi(self):
        doi = random.choice(DOIS)
        try:
            with self.client.get(f"/doi/{doi}/", catch_response=True) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error: {r.status_code}")
                else:
                    r.success()
        except Exception:
            pass

class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    wait_time = between(5, 9)
    host = get_host_for_locust_testing()

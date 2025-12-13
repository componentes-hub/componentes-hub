from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token
import time


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
            with self.client.get("/api/dataset/trending?period=year&limit=100&metric=stars", catch_response=True) as r:
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


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

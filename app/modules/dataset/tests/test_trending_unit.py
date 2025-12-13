from app.modules.dataset.services import DataSetService
from app.modules.dataset import routes as dataset_routes


# Clases dummy usadas para simular objetos reales de base de datos
class _DummyAuthor:
    def __init__(self, name):
        self.name = name


class _DummyMeta:
    def __init__(self, title, doi, authors=None):
        self.title = title
        self.dataset_doi = doi
        self.authors = authors or []


class _DummyDataset:
    def __init__(self, id_, meta, user_id=None):
        self.id = id_
        self.ds_meta_data = meta
        self.user_id = user_id


def test_get_trending_datasets_for_api_happy_path():
    service = DataSetService()

    meta = _DummyMeta(title="Dataset A", doi="10.1/test.1", authors=[_DummyAuthor("Alice")])
    ds = _DummyDataset(1, meta)

    orig_get_trending = DataSetService.get_trending_datasets
    orig_get_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds, 42)]
    DataSetService.get_componenteshub_doi = lambda self, dataset: "http://example/doi/10.1/test.1"

    result = service.get_trending_datasets_for_api(period="week", limit=3, metric="downloads")

    assert isinstance(result, list)
    assert len(result) == 1
    item = result[0]

    assert item["id"] == 1
    assert item["title"] == "Dataset A"
    assert item["author"] == "Alice"
    assert item["url"] == "http://example/doi/10.1/test.1"
    assert item["count"] == 42
    assert item["metric"] == "downloads"

    DataSetService.get_trending_datasets = orig_get_trending
    DataSetService.get_componenteshub_doi = orig_get_doi


def test_get_trending_datasets_for_api_unknown_author():
    service = DataSetService()

    meta = _DummyMeta(title="Dataset B", doi="10.1/test.2", authors=[])
    ds = _DummyDataset(2, meta)

    orig_get_trending = DataSetService.get_trending_datasets
    orig_get_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds, 7)]
    DataSetService.get_componenteshub_doi = lambda self, dataset: "http://example/doi/10.1/test.2"

    result = service.get_trending_datasets_for_api()

    assert result[0]["author"] == "Unknown"

    DataSetService.get_trending_datasets = orig_get_trending
    DataSetService.get_componenteshub_doi = orig_get_doi


def test_get_trending_datasets_first_author():
    service = DataSetService()

    meta = _DummyMeta(
        title="Dataset X",
        doi="10.1/x",
        authors=[_DummyAuthor("Alice"), _DummyAuthor("Bob")]
    )
    ds = _DummyDataset(1, meta)

    orig_get_trending = DataSetService.get_trending_datasets
    orig_get_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds, 10)]
    DataSetService.get_componenteshub_doi = lambda self, dataset: "/doi/10.1/x"

    result = service.get_trending_datasets_for_api()

    assert result[0]["author"] == "Alice"

    DataSetService.get_trending_datasets = orig_get_trending
    DataSetService.get_componenteshub_doi = orig_get_doi


def test_get_trending_datasets_api_route_validation(test_client):
    orig = dataset_routes.dataset_service.get_trending_datasets_for_api
    dataset_routes.dataset_service.get_trending_datasets_for_api = lambda period, limit, metric: []

    try:
        resp = test_client.get("/api/dataset/trending?period=year&limit=100&metric=stars")
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["period"] == "week"
        assert data["metric"] == "downloads"
        assert isinstance(data["trending"], list)
    finally:
        dataset_routes.dataset_service.get_trending_datasets_for_api = orig


def test_api_route_invalid_limit_normalized(test_client):
    captured = {}

    def fake_api(period, limit, metric):
        captured["period"] = period
        captured["limit"] = limit
        captured["metric"] = metric
        return []

    orig = dataset_routes.dataset_service.get_trending_datasets_for_api
    dataset_routes.dataset_service.get_trending_datasets_for_api = fake_api

    try:
        resp = test_client.get("/api/dataset/trending?limit=-5")
        data = resp.get_json()

        assert resp.status_code == 200
        assert captured["limit"] == 3
        assert data["period"] == "week"
        assert data["metric"] == "downloads"
    finally:
        dataset_routes.dataset_service.get_trending_datasets_for_api = orig


def test_api_route_valid_limit_passed(test_client):
    captured = {}

    def fake(period, limit, metric):
        captured["limit"] = limit
        return []

    orig = dataset_routes.dataset_service.get_trending_datasets_for_api
    dataset_routes.dataset_service.get_trending_datasets_for_api = fake
    try:
        resp = test_client.get("/api/dataset/trending?limit=7")
        assert resp.status_code == 200
        assert captured["limit"] == 7
    finally:
        dataset_routes.dataset_service.get_trending_datasets_for_api = orig


def test_api_route_forwards_valid_params(test_client):
    captured = {}

    def fake(period, limit, metric):
        captured["period"] = period
        captured["limit"] = limit
        captured["metric"] = metric
        return []

    orig = dataset_routes.dataset_service.get_trending_datasets_for_api
    dataset_routes.dataset_service.get_trending_datasets_for_api = fake
    try:
        resp = test_client.get("/api/dataset/trending?period=month&limit=2&metric=views")

        assert resp.status_code == 200
        assert captured["period"] == "month"
        assert captured["limit"] == 2
        assert captured["metric"] == "views"
    finally:
        dataset_routes.dataset_service.get_trending_datasets_for_api = orig


def test_ordering_descending_service():
    service = DataSetService()

    meta1 = _DummyMeta("One", "10.1/one", [_DummyAuthor("A")])
    meta2 = _DummyMeta("Two", "10.1/two", [_DummyAuthor("B")])
    meta3 = _DummyMeta("Three", "10.1/three", [_DummyAuthor("C")])

    ds1 = _DummyDataset(1, meta1)
    ds2 = _DummyDataset(2, meta2)
    ds3 = _DummyDataset(3, meta3)

    orig = DataSetService.get_trending_datasets
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds1, 2), (ds2, 5), (ds3, 1)]

    orig_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_componenteshub_doi = lambda self, dataset: f"/doi/{dataset.ds_meta_data.dataset_doi}"

    result = service.get_trending_datasets_for_api()
    counts = [r["count"] for r in result]

    assert counts == [2, 5, 1]

    DataSetService.get_trending_datasets = orig
    DataSetService.get_componenteshub_doi = orig_doi


def test_get_trending_datasets_calls_with_week_views():
    service = DataSetService()

    def fake(self, period, limit, metric):
        assert period == "week"
        assert metric == "views"
        return []

    orig = DataSetService.get_trending_datasets
    DataSetService.get_trending_datasets = fake
    try:
        assert service.get_trending_datasets_for_api(period="week", metric="views") == []
    finally:
        DataSetService.get_trending_datasets = orig


def test_get_trending_datasets_calls_with_month_views():
    service = DataSetService()

    def fake(self, period, limit, metric):
        assert period == "month"
        assert metric == "views"
        return []

    orig = DataSetService.get_trending_datasets
    DataSetService.get_trending_datasets = fake
    try:
        assert service.get_trending_datasets_for_api(period="month", metric="views") == []
    finally:
        DataSetService.get_trending_datasets = orig


def test_empty_trending_list():
    service = DataSetService()
    orig = DataSetService.get_trending_datasets
    DataSetService.get_trending_datasets = lambda self, **kw: []
    try:
        assert service.get_trending_datasets_for_api() == []
    finally:
        DataSetService.get_trending_datasets = orig


def test_missing_fields_in_dataset():
    service = DataSetService()

    meta = _DummyMeta(title=None, doi=None, authors=[])
    ds = _DummyDataset(1, meta)

    orig = DataSetService.get_trending_datasets
    orig_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds, 4)]
    DataSetService.get_componenteshub_doi = lambda self, dataset: None
    try:
        result = service.get_trending_datasets_for_api()

        assert result[0]["title"] is None
        assert result[0]["url"] is None
    finally:
        DataSetService.get_trending_datasets = orig
        DataSetService.get_componenteshub_doi = orig_doi


def test_trending_includes_community_when_present():
    service = DataSetService()

    meta = _DummyMeta(title="WithCommunity", doi="10.1/com", authors=[_DummyAuthor("Carol")])
    ds = _DummyDataset(5, meta, user_id=42)

    orig = DataSetService.get_trending_datasets
    orig_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds, 9)]
    DataSetService.get_componenteshub_doi = lambda self, dataset: "http://example/doi/10.1/com"

    class FakeCommunity:
        def __init__(self, name):
            self.community = type("C", (), {"name": name})()

    fake_query = type("Q", (), {
        "filter_by": staticmethod(
            lambda **kw: type("F", (), {"first": staticmethod(lambda: FakeCommunity("Comunidad X"))})()
        )
    })()

    import app.modules.dataset.services as ds_services
    orig_query = getattr(ds_services.CommunityUser, 'query', None)
    ds_services.CommunityUser.query = fake_query
    try:
        result = service.get_trending_datasets_for_api()
        assert result[0]["community"] == "Comunidad X"
    finally:
        if orig_query is None:
            delattr(ds_services.CommunityUser, 'query')
        else:
            ds_services.CommunityUser.query = orig_query

    DataSetService.get_trending_datasets = orig
    DataSetService.get_componenteshub_doi = orig_doi


def test_trending_community_none_when_absent():
    service = DataSetService()

    meta = _DummyMeta(title="NoCommunity", doi="10.1/nc", authors=[_DummyAuthor("Eve")])
    ds = _DummyDataset(6, meta, user_id=43)

    orig = DataSetService.get_trending_datasets
    orig_doi = DataSetService.get_componenteshub_doi
    DataSetService.get_trending_datasets = lambda self, **kw: [(ds, 1)]
    DataSetService.get_componenteshub_doi = lambda self, dataset: "http://example/doi/10.1/nc"

    fake_query_none = type("Q", (), {
        "filter_by": staticmethod(
            lambda **kw: type("F", (), {"first": staticmethod(lambda: None)})()
        )
    })()

    import app.modules.dataset.services as ds_services
    orig_query = getattr(ds_services.CommunityUser, 'query', None)
    ds_services.CommunityUser.query = fake_query_none
    try:
        result = service.get_trending_datasets_for_api()
        assert result[0]["community"] is None
    finally:
        if orig_query is None:
            delattr(ds_services.CommunityUser, 'query')
        else:
            ds_services.CommunityUser.query = orig_query

    DataSetService.get_trending_datasets = orig
    DataSetService.get_componenteshub_doi = orig_doi

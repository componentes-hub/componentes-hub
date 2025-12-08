from app.modules.dataset.services import DataSetService
from app.modules.dataset import routes as dataset_routes


# Creamos estas clases para simular modelos reales de la base de datos


class _DummyAuthor:
    def __init__(self, name):
        self.name = name


class _DummyMeta:
    def __init__(self, title, doi, authors=None):
        self.title = title
        self.dataset_doi = doi
        self.authors = authors or []


class _DummyDataset:
    def __init__(self, id_, meta):
        self.id = id_
        self.ds_meta_data = meta


def test_get_trending_datasets_for_api_happy_path(monkeypatch):
    service = DataSetService()

    meta = _DummyMeta(title="Dataset A", doi="10.1/test.1", authors=[_DummyAuthor("Alice")])
    ds = _DummyDataset(1, meta)

    monkeypatch.setattr(DataSetService, "get_trending_datasets",
                        lambda self, **kw: [(ds, 42)])

    monkeypatch.setattr(DataSetService, "get_componenteshub_doi",
                        lambda self, dataset: "http://example/doi/10.1/test.1")

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


def test_get_trending_datasets_for_api_unknown_author(monkeypatch):
    service = DataSetService()

    meta = _DummyMeta(title="Dataset B", doi="10.1/test.2", authors=[])
    ds = _DummyDataset(2, meta)

    monkeypatch.setattr(DataSetService, "get_trending_datasets",
                        lambda self, **kw: [(ds, 7)])

    monkeypatch.setattr(DataSetService, "get_componenteshub_doi",
                        lambda self, dataset: "http://example/doi/10.1/test.2")

    result = service.get_trending_datasets_for_api()

    assert result[0]["author"] == "Unknown"


def test_get_trending_datasets_first_author(monkeypatch):
    service = DataSetService()

    meta = _DummyMeta(
        title="Dataset X",
        doi="10.1/x",
        authors=[_DummyAuthor("Alice"), _DummyAuthor("Bob")]
    )
    ds = _DummyDataset(1, meta)

    monkeypatch.setattr(DataSetService, "get_trending_datasets",
                        lambda self, **kw: [(ds, 10)])

    monkeypatch.setattr(DataSetService, "get_componenteshub_doi",
                        lambda self, dataset: "/doi/10.1/x")

    result = service.get_trending_datasets_for_api()

    assert result[0]["author"] == "Alice"


def test_get_trending_datasets_api_route_validation(test_client, monkeypatch):

    monkeypatch.setattr(dataset_routes.dataset_service,
                        "get_trending_datasets_for_api",
                        lambda period, limit, metric: [])

    resp = test_client.get("/api/dataset/trending?period=year&limit=100&metric=stars")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["period"] == "week"
    assert data["metric"] == "downloads"
    assert isinstance(data["trending"], list)


def test_api_route_invalid_limit_normalized(test_client, monkeypatch):

    captured = {}

    # Esta función captura el limit que recibe la ruta
    def fake_api(period, limit, metric):
        captured["period"] = period
        captured["limit"] = limit
        captured["metric"] = metric
        return []

    monkeypatch.setattr(dataset_routes.dataset_service,
                        "get_trending_datasets_for_api",
                        fake_api)

    resp = test_client.get("/api/dataset/trending?limit=-5")
    data = resp.get_json()

    assert resp.status_code == 200
    # La ruta normaliza limit inválido (<1) a 3
    assert captured["limit"] == 3
    # La ruta normaliza period y metric si vienen inválidos por defecto
    assert data["period"] == "week"
    assert data["metric"] == "downloads"


def test_api_route_valid_limit_passed(test_client, monkeypatch):
    captured = {}

    def fake(period, limit, metric):
        captured["limit"] = limit
        return []

    monkeypatch.setattr(dataset_routes.dataset_service,
                        "get_trending_datasets_for_api", fake)

    resp = test_client.get("/api/dataset/trending?limit=7")
    assert resp.status_code == 200
    assert captured["limit"] == 7
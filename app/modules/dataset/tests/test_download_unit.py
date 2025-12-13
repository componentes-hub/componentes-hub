from app.modules.dataset.services import DataSetService


class _DummyRequest:
    def __init__(self, cookies=None, remote_addr="127.0.0.1"):
        self.cookies = cookies or {}
        self.remote_addr = remote_addr


class _DummyDownloadCounter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1


class _DummyDataset:
    def __init__(self, id_):
        self.id = id_
        self.downloads = _DummyDownloadCounter()


def test_register_download_increments_counter():
    service = DataSetService()
    dataset = _DummyDataset(1)
    request = _DummyRequest()

    # Simulamos el método real que incrementa el contador
    orig = getattr(service, "register_download", None)

    def fake_register(ds, req):
        ds.downloads.increment()

    service.register_download = fake_register

    service.register_download(dataset, request)

    assert dataset.downloads.count == 1

    if orig:
        service.register_download = orig



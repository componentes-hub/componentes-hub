from app.modules.dataset.services import DataSetService

class _DummyViewCounter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1


class _DummyFile:
    def __init__(self, size):
        self.size = size


class _DummyDataset:
    def __init__(self, id_, files=None):
        self.id = id_
        self._downloads = 0
        self._views = _DummyViewCounter()
        self.files = files or []

    def get_download_count(self):
        return self._downloads

    def increment_downloads(self):
        self._downloads += 1

    def get_files_count(self):
        return len(self.files)

    def get_file_total_size(self):
        return sum(f.size for f in self.files)

def test_get_download_count_returns_correct_value():
    service = DataSetService()
    dataset = _DummyDataset(1)

    dataset.increment_downloads()
    dataset.increment_downloads()

    orig = getattr(service, "get_download_count", None)
    service.get_download_count = lambda ds: ds.get_download_count()

    count = service.get_download_count(dataset)

    assert count == 2

    if orig:
        service.get_download_count = orig


def test_views_are_counted_correctly():
    service = DataSetService()
    dataset = _DummyDataset(2)

    dataset._views.increment()
    dataset._views.increment()
    dataset._views.increment()

    orig = getattr(service, "get_view_count", None)
    service.get_view_count = lambda ds: ds._views.count

    views = service.get_view_count(dataset)

    assert views == 3

    if orig:
        service.get_view_count = orig


def test_files_count_is_correct():
    service = DataSetService()
    files = [_DummyFile(100), _DummyFile(200), _DummyFile(300)]
    dataset = _DummyDataset(3, files=files)

    orig = getattr(service, "get_files_count", None)
    service.get_files_count = lambda ds: ds.get_files_count()

    count = service.get_files_count(dataset)

    assert count == 3

    if orig:
        service.get_files_count = orig


def test_total_size_is_calculated_correctly():
    service = DataSetService()
    files = [_DummyFile(512), _DummyFile(1024)]
    dataset = _DummyDataset(4, files=files)

    orig = getattr(service, "get_total_size", None)
    service.get_total_size = lambda ds: ds.get_file_total_size()

    size = service.get_total_size(dataset)

    assert size == 1536

    if orig:
        service.get_total_size = orig


def test_empty_dataset_has_zero_stats():
    service = DataSetService()
    dataset = _DummyDataset(5)

    orig_downloads = getattr(service, "get_download_count", None)
    orig_views = getattr(service, "get_view_count", None)
    orig_files = getattr(service, "get_files_count", None)
    orig_size = getattr(service, "get_total_size", None)

    service.get_download_count = lambda ds: ds.get_download_count()
    service.get_view_count = lambda ds: ds._views.count
    service.get_files_count = lambda ds: ds.get_files_count()
    service.get_total_size = lambda ds: ds.get_file_total_size()

    assert service.get_download_count(dataset) == 0
    assert service.get_view_count(dataset) == 0
    assert service.get_files_count(dataset) == 0
    assert service.get_total_size(dataset) == 0

    if orig_downloads:
        service.get_download_count = orig_downloads
    if orig_views:
        service.get_view_count = orig_views
    if orig_files:
        service.get_files_count = orig_files
    if orig_size:
        service.get_total_size = orig_size
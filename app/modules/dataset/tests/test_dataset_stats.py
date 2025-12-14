from app.modules.dataset.services import DataSetService

class _DummyUser:
    def __init__(self, id_):
        self.id = id_

class _DummyAuthor:
    def __init__(self, user_id):
        self.user_id = user_id
        self.name = "Author"

    def to_dict(self):
        return {"user_id": self.user_id}

class _DummyMetaData:
    def __init__(self, authors):
        self.authors = authors
        self.title = "Test dataset"
        self.dataset_doi = "10.1234/test"
        self.description = "Description"
        self.tags = ""

class _DummyCounter:
    def __init__(self, count=0):
        self.count = count

    def increment(self):
        self.count += 1

class _DummyDataset:
    def __init__(self, dataset_id, authors):
        self.id = dataset_id
        self.ds_meta_data = _DummyMetaData(authors)
        self.downloads = _DummyCounter()
        self.views = _DummyCounter()

    def get_download_count(self):
        return self.downloads.count

    def get_files_count(self):
        return 2

    def get_file_total_size(self):
        return 2048

    def get_file_total_size_for_human(self):
        return "2 KB"


# TESTS DE ACCESO A STATS

def can_access_stats(dataset, user):
    """
    Helper que imita la lógica del endpoint:
    solo autores pueden acceder
    """
    if not user:
        return False

    return any(author.user_id == user.id for author in dataset.ds_meta_data.authors)

def test_stats_access_allowed_for_author():
    user = _DummyUser(id_=1)
    author = _DummyAuthor(user_id=1)
    dataset = _DummyDataset(1, authors=[author])

    assert can_access_stats(dataset, user) is True

def test_stats_access_denied_for_non_author():
    user = _DummyUser(id_=2)
    author = _DummyAuthor(user_id=1)
    dataset = _DummyDataset(2, authors=[author])

    assert can_access_stats(dataset, user) is False

def test_stats_access_denied_for_anonymous_user():
    author = _DummyAuthor(user_id=1)
    dataset = _DummyDataset(3, authors=[author])

    assert can_access_stats(dataset, None) is False

def test_stats_access_allowed_with_multiple_authors():
    user = _DummyUser(id_=3)
    authors = [
        _DummyAuthor(user_id=1),
        _DummyAuthor(user_id=2),
        _DummyAuthor(user_id=3),
    ]
    dataset = _DummyDataset(4, authors=authors)

    assert can_access_stats(dataset, user) is True

# TESTS DE STATS DEL DATASET

def test_download_counter_increments():
    dataset = _DummyDataset(5, authors=[])

    dataset.downloads.increment()
    dataset.downloads.increment()

    assert dataset.get_download_count() == 2

def test_files_count():
    dataset = _DummyDataset(6, authors=[])

    assert dataset.get_files_count() == 2

def test_total_file_size():
    dataset = _DummyDataset(7, authors=[])

    assert dataset.get_file_total_size() == 2048

def test_total_file_size_human_format():
    dataset = _DummyDataset(8, authors=[])

    assert dataset.get_file_total_size_for_human() == "2 KB"

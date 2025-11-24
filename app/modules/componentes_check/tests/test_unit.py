import pytest
from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.componentes_check.check_comp import PCCompFileChecker


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Crea el usuario sobre el que podríamos correr tests que necesiten sesión
        user_test = User(email="user@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

    yield test_client


def test_sample_assertion(test_client):
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_empty_comp_file(test_client):
    """Empty content should produce an error and be invalid."""
    checker = PCCompFileChecker("")
    assert not checker.is_valid()
    assert any("El archivo está vacío" in e for e in checker.get_errors())


def test_missing_properties_section(test_client):
    """If properties section is missing, validator reports it."""
    content = """
    name: TestComp
    version: 1.0
    author: Tester
    """
    checker = PCCompFileChecker(content)
    assert not checker.is_valid()


def test_missing_required_property(test_client):
    """Properties block missing required fields should report missing property errors."""
    content = """
    name: TestComp
    version: 1.0
    author: Tester
    properties:
        type: processor
        model: Intel i9
        description: A test processor
    """
    checker = PCCompFileChecker(content)
    assert not checker.is_valid()
    # 'id' is missing
    assert any("Falta la propiedad obligatoria: 'id'" in e for e in checker.get_errors())


def test_invalid_type_and_malformed_property(test_client):
    """Invalid component type and malformed property lines are caught."""
    content = """
    name: TestComp
    version: 1.0
    author: Tester
    properties:
        id: 123
        type: unknown_type
        model: SomeModel
        description: Something
        badline without colon
    """
    checker = PCCompFileChecker(content)
    assert not checker.is_valid()
    assert any("Tipo de componente no válido" in e for e in checker.get_errors())
    assert any("Propiedad mal formada" in e for e in checker.get_errors())


def test_valid_processor_comp_file(test_client):
    """A correct processor .comp file should be valid and parsed correctly."""
    content = """
    name: MyProcessor
    version: 2.0
    author: ACME
    properties:
        id: proc-001
        type: processor
        model: Intel i7-10700K
        description: High performance CPU
    """
    checker = PCCompFileChecker(content)
    assert checker.is_valid(), f"Errors found: {checker.get_errors()}"
    parsed = checker.get_parsed_data()
    assert parsed["name"] == "MyProcessor"
    assert parsed["version"] == "2.0"
    assert parsed["author"] == "ACME"
    assert parsed["properties"]["id"] == "proc-001"
    assert parsed["properties"]["type"] == "processor"

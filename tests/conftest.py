import pytest


@pytest.fixture
def service_name():
    return 'sls-tools-param-store-test'


@pytest.fixture
def service_stage():
    return 'test'


@pytest.fixture(autouse=True)
def setup_env_vars(monkeypatch, service_name, service_stage):
    monkeypatch.setenv('SERVICE_NAME', service_name)
    monkeypatch.setenv('SERVICE_STAGE', service_stage)
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-west-2')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'fake-key-aws-is-mocked-in-tests-but-needs-this-var')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'fake-secret-aws-is-mocked-in-tests-but-needs-this-var')

import pytest
import os
import uuid
from moto import mock_ssm
from src.sls_tools.param_store import ParamStore


@pytest.fixture
def key():
    return 'TEST-KEY'


@pytest.fixture
def value():
    return str(uuid.uuid4())


@pytest.fixture(scope="function", autouse=True)
@mock_ssm
def reset_key_value(key):
    """
    Delete the test key before each test method is executed.
    """
    ParamStore.delete(key, store=ParamStore.Stores.AUTO)
    assert key not in os.environ.keys()
    assert ParamStore.get(key).value is None
    assert ParamStore.get(key, store=ParamStore.Stores.OS).value is None
    assert ParamStore.get(key, store=ParamStore.Stores.SSM).value is None


def test__get_ssm_client(mocker):
    assert str(type(ParamStore._get_ssm_client())) == "<class 'botocore.client.SSM'>"

    # Reset the cached ssm_client
    ParamStore._ssm_client = None
    mocker.patch('boto3.client', side_effect=Exception('fail'))
    assert ParamStore._get_ssm_client() is None


def test__build_ssm_key(monkeypatch):
    monkeypatch.setenv('SERVICE_NAME', 'a')
    monkeypatch.setenv('SERVICE_STAGE', 'b')
    assert ParamStore._build_ssm_key('c') == '/a/b/c'

    monkeypatch.delenv('SERVICE_NAME')
    with pytest.raises(ValueError) as ex:
        ParamStore._build_ssm_key('c')
    assert str(ex.value) == 'Environment variable not set: SERVICE_NAME'

    # Reset...
    monkeypatch.setenv('SERVICE_NAME', 'a')
    monkeypatch.setenv('SERVICE_STAGE', 'b')

    monkeypatch.delenv('SERVICE_STAGE')
    with pytest.raises(ValueError) as ex:
        ParamStore._build_ssm_key('c')
    assert str(ex.value) == 'Environment variable not set: SERVICE_STAGE'


@mock_ssm
def test_it_sets_and_gets_in_the_os(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.OS)

    assert key in os.environ.keys()
    assert ParamStore.get(key).value == value
    assert ParamStore.get(key, store=ParamStore.Stores.OS).value == value
    assert ParamStore.get(key, store=ParamStore.Stores.SSM).value is None


@mock_ssm
def test_it_sets_and_gets_in_ssm(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.SSM)

    assert key not in os.environ.keys()
    assert ParamStore.get(key).value == value
    assert ParamStore.get(key, store=ParamStore.Stores.OS).value is None
    assert ParamStore.get(key, store=ParamStore.Stores.SSM).value == value


@mock_ssm
def test_it_sets_and_gets_in_os_and_ssm(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.AUTO)

    assert key in os.environ.keys()
    assert ParamStore.get(key).value == value
    assert ParamStore.get(key, store=ParamStore.Stores.OS).value == value
    assert ParamStore.get(key, store=ParamStore.Stores.SSM).value == value


@mock_ssm
def test_it_returns_the_default_value(key, value):
    assert ParamStore.delete(key)
    default_value = 'a-default-value'
    assert ParamStore.get(key, default=default_value).value == default_value


@mock_ssm
def test_it_returns_the_value_from_os_when_both_stores_are_set(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.OS)
    assert ParamStore.set(key, str(uuid.uuid4()), store=ParamStore.Stores.SSM)
    assert ParamStore.get(key).value == value


@mock_ssm
def test_it_deletes_the_key_from_os(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.OS)
    assert ParamStore.get(key).value == value

    assert ParamStore.delete(key, store=ParamStore.Stores.OS)
    assert ParamStore.get(key).value is None


@mock_ssm
def test_it_deletes_a_missing_key_from_os(key):
    assert ParamStore.get(key, store=ParamStore.Stores.OS).value is None
    assert ParamStore.delete(key, store=ParamStore.Stores.OS) is True


@mock_ssm
def test_it_deletes_the_key_from_ssm(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.SSM)
    assert ParamStore.get(key).value == value

    assert ParamStore.delete(key, store=ParamStore.Stores.SSM)
    assert ParamStore.get(key).value is None


@mock_ssm
def test_it_deletes_a_missing_key_from_ssm(key):
    assert ParamStore.get(key, store=ParamStore.Stores.SSM).value is None
    assert ParamStore.delete(key, store=ParamStore.Stores.SSM) is True


@mock_ssm
def test_it_deletes_the_key_from_os_and_ssm(key, value):
    assert ParamStore.set(key, value, store=ParamStore.Stores.AUTO)
    assert ParamStore.get(key, store=ParamStore.Stores.OS).value == value
    assert ParamStore.get(key, store=ParamStore.Stores.SSM).value == value

    assert ParamStore.delete(key, store=ParamStore.Stores.AUTO)
    assert ParamStore.get(key).value is None

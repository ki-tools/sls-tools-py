import pytest
import os
import uuid
import logging
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
    assert ParamStore.contains(key) is False
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
def test_it_contains_a_key(key, value):
    assert ParamStore.contains(key) is False

    ParamStore.set(key, value, store=ParamStore.Stores.OS)
    assert ParamStore.contains(key) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.OS) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.AUTO) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.SSM) is False

    ParamStore.delete(key)
    assert ParamStore.contains(key) is False

    ParamStore.set(key, value, store=ParamStore.Stores.SSM)
    assert ParamStore.contains(key) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.OS) is False
    assert ParamStore.contains(key, store=ParamStore.Stores.AUTO) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.SSM) is True

    ParamStore.delete(key)
    assert ParamStore.contains(key) is False

    ParamStore.set(key, value, store=ParamStore.Stores.AUTO)
    assert ParamStore.contains(key) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.OS) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.AUTO) is True
    assert ParamStore.contains(key, store=ParamStore.Stores.SSM) is True


@mock_ssm
def test_it_does_not_raise_when_getting_an_unset_ssm_key(key):
    default_value = str(uuid.uuid4())
    assert ParamStore.get(key, default=default_value).value == default_value


@mock_ssm
def test_it_logs_ssm_parameter_missing_errors_when_getting(key, mocker):
    with mocker.mock_module.patch.object(logging, 'exception') as log_mock:
        default_value = str(uuid.uuid4())
        assert ParamStore.get(key, default=default_value).value == default_value
        assert log_mock.called is True
        assert 'SSM Parameter Not Found:' in log_mock.call_args[0][0]


@mock_ssm
def test_it_does_not_raise_general_ssm_errors_when_getting(key, mocker):
    with mocker.mock_module.patch.object(ParamStore._get_ssm_client(), 'get_parameter') as mock:
        mock.side_effect = Exception('Random Error...')
        default_value = str(uuid.uuid4())
        assert ParamStore.get(key, default=default_value).value == default_value
        assert mock.called is True


@mock_ssm
def test_it_logs_general_ssm_get_errors(key, mocker):
    with mocker.mock_module.patch.object(logging, 'exception') as log_mock:
        with mocker.mock_module.patch.object(ParamStore._get_ssm_client(), 'get_parameter') as mock:
            mock.side_effect = Exception('Random Error...')
            default_value = str(uuid.uuid4())
            assert ParamStore.get(key, default=default_value).value == default_value
            assert mock.called is True

        assert log_mock.called is True
        assert log_mock.call_args[0][0] == 'SSM Error: Random Error...'


@mock_ssm
def test_it_logs_general_ssm_set_errors(key, mocker):
    with mocker.mock_module.patch.object(logging, 'exception') as log_mock:
        with mocker.mock_module.patch.object(ParamStore._get_ssm_client(), 'put_parameter') as mock:
            mock.side_effect = Exception('Random Error...')
            assert ParamStore.set(key, value, store=ParamStore.Stores.SSM) is False
            assert mock.called is True

        assert log_mock.called is True
        assert log_mock.call_args[0][0] == 'SSM Error: Random Error...'


@mock_ssm
def test_it_logs_general_ssm_delete_errors(key, mocker):
    with mocker.mock_module.patch.object(logging, 'exception') as log_mock:
        with mocker.mock_module.patch.object(ParamStore._get_ssm_client(), 'delete_parameter') as mock:
            mock.side_effect = Exception('Random Error...')
            assert ParamStore.delete(key, store=ParamStore.Stores.SSM) is False
            assert mock.called is True

        assert log_mock.called is True
        assert log_mock.call_args[0][0] == 'SSM Error: Random Error...'


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

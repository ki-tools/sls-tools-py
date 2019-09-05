import pytest
import uuid
from src.sls_tools.param_store import ParamStore, ParamStoreResult


@pytest.fixture
def key():
    return 'TEST-KEY'


@pytest.fixture
def value():
    return str(uuid.uuid4())


@pytest.fixture
def param_store_result(key, value):
    return ParamStoreResult(key, value, None)


def test_it_has_the_key(param_store_result, key):
    assert param_store_result.key == key


def test_it_has_the_value(param_store_result, value):
    assert param_store_result.value == value


def test_it_has_the_store(param_store_result, key, value):
    assert param_store_result.store is None
    assert ParamStoreResult(key, value, ParamStore.Stores.SSM).store == ParamStore.Stores.SSM


def test_it_converts_to_int(key):
    assert ParamStoreResult(key, '100', None).to_int() == 100
    assert ParamStoreResult(key, '0200', None).to_int() == 200
    assert ParamStoreResult(key, 3, None).to_int() == 3
    assert ParamStoreResult(key, '   ', None).to_int() is None
    assert ParamStoreResult(key, None, None).to_int() is None


def test_it_errors_when_converting_non_int_strings(key):
    for bad_string in ['not a number', 'one', 'a', '.1', '1.0']:
        with pytest.raises(ValueError) as ex:
            ParamStoreResult(key, bad_string, None).to_int()
        assert 'invalid literal for int()' in str(ex.value)


def test_it_converts_to_float(key):
    assert ParamStoreResult(key, '100.001', None).to_float() == 100.001
    assert ParamStoreResult(key, '02.00', None).to_float() == 2.00
    assert ParamStoreResult(key, '0300', None).to_float() == 300
    assert ParamStoreResult(key, 40.0, None).to_float() == 40.0
    assert ParamStoreResult(key, '   ', None).to_float() is None
    assert ParamStoreResult(key, None, None).to_float() is None


def test_it_errors_when_converting_non_float_strings(key):
    for bad_string in ['not a number', 'one', 'a']:
        with pytest.raises(ValueError) as ex:
            ParamStoreResult(key, bad_string, None).to_float()
        assert 'could not convert string to float:' in str(ex.value)


def test_it_converts_to_bool(key):
    for bool_value in ['true', 'True', '  tRUe  ', 't', '1', True]:
        assert ParamStoreResult(key, bool_value, None).to_bool() is True

    for non_bool_value in ['false', 'False', 'fAlSe', 'f', '0', '   ', None]:
        assert ParamStoreResult(key, non_bool_value, None).to_bool() is False


def test_it_uses_custom_true_values(key):
    assert ParamStoreResult(key, 'False', None).to_bool(true_values=['False']) is True


def test_it_converts_to_list(key):
    value = '1, a , abcd,,   ,'
    expected_value = ['1', 'a', 'abcd']
    assert ParamStoreResult(key, value, None).to_list() == expected_value
    assert ParamStoreResult(key, '', None).to_list() == []
    assert ParamStoreResult(key, None, None).to_list() == []


def test_it_uses_a_custom_delimiter_to_list():
    assert ParamStoreResult(key, 'a|b|c', None).to_list(delimiter='|') == ['a', 'b', 'c']

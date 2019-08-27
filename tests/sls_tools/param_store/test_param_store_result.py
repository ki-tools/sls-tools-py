import pytest
import uuid
from src.sls_tools.param_store import ParamStoreResult


@pytest.fixture
def key():
    return 'TEST-KEY'


@pytest.fixture
def value():
    return str(uuid.uuid4())


@pytest.fixture
def param_store_result(key, value):
    return ParamStoreResult(key, value)


def test_it_has_the_key(param_store_result, key):
    assert param_store_result.key == key


def test_it_has_the_value(param_store_result, value):
    assert param_store_result.value == value


def test_it_converts_to_int(key):
    assert ParamStoreResult(key, '100').to_int() == 100
    assert ParamStoreResult(key, '0200').to_int() == 200
    assert ParamStoreResult(key, 3).to_int() == 3
    assert ParamStoreResult(key, '   ').to_int() is None
    assert ParamStoreResult(key, None).to_int() is None


def test_it_errors_when_converting_non_int_strings(key):
    for bad_string in ['not a number', 'one', 'a', '.1', '1.0']:
        with pytest.raises(ValueError) as ex:
            ParamStoreResult(key, bad_string).to_int()
        assert 'invalid literal for int()' in str(ex.value)


def test_it_converts_to_float(key):
    assert ParamStoreResult(key, '100.001').to_float() == 100.001
    assert ParamStoreResult(key, '02.00').to_float() == 2.00
    assert ParamStoreResult(key, '0300').to_float() == 300
    assert ParamStoreResult(key, 40.0).to_float() == 40.0
    assert ParamStoreResult(key, '   ').to_float() is None
    assert ParamStoreResult(key, None).to_float() is None


def test_it_errors_when_converting_non_float_strings(key):
    for bad_string in ['not a number', 'one', 'a']:
        with pytest.raises(ValueError) as ex:
            ParamStoreResult(key, bad_string).to_float()
        assert 'could not convert string to float:' in str(ex.value)


def test_it_converts_to_bool(key):
    for bool_value in ['true', 'True', '  tRUe  ', 't', '1', True]:
        assert ParamStoreResult(key, bool_value).to_bool() is True

    for non_bool_value in ['false', 'False', 'fAlSe', 'f', '0', '   ', None]:
        assert ParamStoreResult(key, non_bool_value).to_bool() is False


def test_it_uses_custom_true_values(key):
    assert ParamStoreResult(key, 'False').to_bool(true_values=['False']) is True


def test_it_converts_to_list(key):
    value = '1, a , abcd,,   ,'
    expected_value = ['1', 'a', 'abcd']
    assert ParamStoreResult(key, value).to_list() == expected_value
    assert ParamStoreResult(key, '').to_list() == []
    assert ParamStoreResult(key, None).to_list() == []


def test_it_uses_a_custom_delimiter_to_list():
    assert ParamStoreResult(key, 'a|b|c').to_list(delimiter='|') == ['a', 'b', 'c']

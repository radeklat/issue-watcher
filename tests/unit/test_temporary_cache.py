import os
from time import time
from typing import Dict, List, Union
from unittest.mock import patch

import pytest
from ujson import dumps, loads

from issuewatcher.temporary_cache import TemporaryCache

_PROJECT = "radeklat/issue-watcher"
_KEY_IN = "1"
_KEY_OUT = "1"
_VALUE = "test value"


def _create_temp_file(value: Union[str, Dict, List] = ""):
    with open(TemporaryCache._TEMP_FILE_NAME, "w") as temp_file:
        temp_file.write(value if isinstance(value, str) else dumps(value))


def _remove_temp_file():
    try:
        os.remove(TemporaryCache._TEMP_FILE_NAME)
    except FileNotFoundError:
        pass


def _read_temp_file() -> str:
    with open(TemporaryCache._TEMP_FILE_NAME, "r") as temp_file:
        return temp_file.read()


def _get_instance() -> TemporaryCache:
    return TemporaryCache(_PROJECT)


class TestTempCache:
    @staticmethod
    def test_it_can_read_from_a_file():
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})
        assert _get_instance()[_KEY_IN] == _VALUE

    @staticmethod
    def test_it_can_write_into_a_file():
        _create_temp_file()
        with patch("time.time", return_value=10):
            _get_instance()[_KEY_IN] = _VALUE
        assert loads(_read_temp_file()) == {_PROJECT: {_KEY_OUT: [_VALUE, 10]}}

    @staticmethod
    def test_it_raises_key_error_when_key_is_missing():
        _create_temp_file()
        with pytest.raises(KeyError):
            _value = _get_instance()[_KEY_IN]

    @staticmethod
    def test_it_ignores_non_json_file():
        _create_temp_file('asdjfkk{:}:""')
        with patch("time.time", return_value=10):
            _get_instance()[_KEY_IN] = _VALUE
        assert loads(_read_temp_file()) == {_PROJECT: {_KEY_OUT: [_VALUE, 10]}}

    @staticmethod
    def test_it_ignores_json_file_without_top_level_dict():
        _create_temp_file([1, 2, 3, 4])
        with patch("time.time", return_value=10):
            _get_instance()[_KEY_IN] = _VALUE
        assert loads(_read_temp_file()) == {_PROJECT: {_KEY_OUT: [_VALUE, 10]}}

    @staticmethod
    def test_it_ignores_missing_file():
        _remove_temp_file()

        with pytest.raises(KeyError):
            _value = _get_instance()[_KEY_IN]

    @staticmethod
    def test_it_can_be_cleared():
        _create_temp_file({_PROJECT: {_KEY_OUT: _VALUE}})
        _get_instance().clear()
        assert loads(_read_temp_file()) == {}

    @staticmethod
    def test_it_separates_projects():
        _remove_temp_file()

        class TestCache(TemporaryCache):
            pass

        with patch("time.time", return_value=10):
            TestCache(_PROJECT)[_KEY_IN] = _VALUE
            TestCache(_PROJECT + "x")[_KEY_IN] = _VALUE

        assert loads(_read_temp_file()) == {
            _PROJECT: {_KEY_OUT: [_VALUE, 10]},
            _PROJECT + "x": {_KEY_OUT: [_VALUE, 10]},
        }


class TestTempCacheGet:
    @staticmethod
    @pytest.fixture(autouse=True)
    def set_up():
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})

    @staticmethod
    def test_it_returns_value_if_exists():
        assert _get_instance().get(_KEY_IN) == _VALUE

    @staticmethod
    def test_it_returns_none_by_default_when_key_is_missing():
        assert _get_instance().get("2") is None

    @staticmethod
    def test_it_returns_custom_default_value_when_key_is_missing():
        assert _get_instance().get("3", _VALUE) == _VALUE


_WRONG_EXPIRY_VALUES = [
    pytest.param("-5", id="negative number"),
    pytest.param("some string", id="not a number"),
    pytest.param("", id="empty string"),
]


class TestCacheInvalidation:
    @staticmethod
    def test_it_is_set_to_one_day_in_seconds_by_default():
        with patch.dict("os.environ", {}):
            assert _get_instance()._expire_in_seconds == 3600

    @staticmethod
    def test_it_can_be_overriden_with_environment_variable():
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: "10"}):
            assert _get_instance()._expire_in_seconds == 10

    @staticmethod
    @pytest.mark.parametrize("value", _WRONG_EXPIRY_VALUES)
    def test_it_warns_when_environment_variable_is(value):
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: value}):
            with pytest.warns(RuntimeWarning, match=".*improperly configured.*"):
                _get_instance()

    @staticmethod
    @pytest.mark.parametrize("value", _WRONG_EXPIRY_VALUES)
    def test_it_ignores_invalid_environment_variable_value(value):
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: value}):
            with pytest.warns(RuntimeWarning, match=".*Using default value of.*"):
                _get_instance()

    @staticmethod
    def test_it_will_not_return_expired_entry():
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, 0]}})
        assert _get_instance().get(_KEY_IN) is None

    @staticmethod
    def test_it_will_return_valid_entry():
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})
        assert _get_instance().get(_KEY_IN) == _VALUE

    @staticmethod
    def test_it_doesnt_write_to_cache_when_disabled():
        _remove_temp_file()
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: "0"}):
            _get_instance()[_KEY_IN] = _VALUE
        assert not os.path.isfile(TemporaryCache._TEMP_FILE_NAME)

    @staticmethod
    def test_it_doesnt_read_cache_when_disabled():
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: "0"}):
            assert _get_instance().get(_KEY_IN) is None

    @staticmethod
    @pytest.mark.parametrize("value", _WRONG_EXPIRY_VALUES)
    def test_it_ignores_invalid_expiry_cache_value_(value):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, value]}})
        assert _get_instance().get(_KEY_IN) is None

import os
from time import time
from typing import Dict, List, Union
from unittest import TestCase
from unittest.mock import patch

from parameterized import parameterized
from ujson import dumps, loads

from temporary_cache import TemporaryCache
from tests.helpers.parameterized import get_test_case_name_without_index

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


class TempCache(TestCase):
    def test_it_can_read_from_a_file(self):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})
        self.assertEqual(_get_instance()[_KEY_IN], _VALUE)

    def test_it_can_write_into_a_file(self):
        _create_temp_file()
        with patch("time.time", return_value=10):
            _get_instance()[_KEY_IN] = _VALUE
        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {_KEY_OUT: [_VALUE, 10]}})

    def test_it_raises_key_error_when_key_is_missing(self):
        _create_temp_file()
        with self.assertRaises(KeyError):
            _value = _get_instance()[_KEY_IN]

    def test_it_ignores_non_json_file(self):
        _create_temp_file('asdjfkk{:}:""')
        with patch("time.time", return_value=10):
            _get_instance()[_KEY_IN] = _VALUE
        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {_KEY_OUT: [_VALUE, 10]}})

    def test_it_ignores_json_file_without_top_level_dict(self):
        _create_temp_file([1, 2, 3, 4])
        with patch("time.time", return_value=10):
            _get_instance()[_KEY_IN] = _VALUE
        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {_KEY_OUT: [_VALUE, 10]}})

    def test_it_ignores_missing_file(self):
        _remove_temp_file()

        with self.assertRaises(KeyError):
            _value = _get_instance()[_KEY_IN]

    def test_it_can_be_cleared(self):
        _create_temp_file({_PROJECT: {_KEY_OUT: _VALUE}})
        _get_instance().clear()
        self.assertDictEqual(loads(_read_temp_file()), {})

    def test_it_separates_projects(self):
        _remove_temp_file()

        class TestCache(TemporaryCache):
            pass

        with patch("time.time", return_value=10):
            TestCache(_PROJECT)[_KEY_IN] = _VALUE
            TestCache(_PROJECT + "x")[_KEY_IN] = _VALUE

        self.assertDictEqual(
            loads(_read_temp_file()),
            {_PROJECT: {_KEY_OUT: [_VALUE, 10]}, _PROJECT + "x": {_KEY_OUT: [_VALUE, 10]}},
        )


class TempCacheGet(TestCase):
    def setUp(self):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})

    def test_it_returns_value_if_exists(self):
        self.assertEqual(_get_instance().get(_KEY_IN), _VALUE)

    def test_it_returns_none_by_default_when_key_is_missing(self):
        self.assertIsNone(_get_instance().get("2"))

    def test_it_returns_custom_default_value_when_key_is_missing(self):
        self.assertEqual(_get_instance().get("3", _VALUE), _VALUE)


_WRONG_EXPIRY_VALUES = [
    ("negative number", "-5"),
    ("not a number", "some string"),
    ("empty string", ""),
]


class CacheInvalidation(TestCase):
    def test_it_is_set_to_one_day_in_seconds_by_default(self):
        with patch.dict("os.environ", {}):
            self.assertEqual(_get_instance()._expire_in_seconds, 3600)

    def test_it_can_be_overriden_with_environment_variable(self):
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: "10"}):
            self.assertEqual(_get_instance()._expire_in_seconds, 10)

    @parameterized.expand(_WRONG_EXPIRY_VALUES, name_func=get_test_case_name_without_index)
    def test_it_warns_when_environment_variable_is(self, _name, value):
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: value}):
            with self.assertWarnsRegex(RuntimeWarning, ".*improperly configured.*"):
                _get_instance()

    @parameterized.expand(_WRONG_EXPIRY_VALUES, name_func=get_test_case_name_without_index)
    def test_it_ignores_invalid_environment_variable_value(self, _name, value):
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: value}):
            with self.assertWarnsRegex(RuntimeWarning, ".*Using default value of.*"):
                _get_instance()

    def test_it_will_not_return_expired_entry(self):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, 0]}})
        self.assertIsNone(_get_instance().get(_KEY_IN))

    def test_it_will_return_valid_entry(self):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})
        self.assertEqual(_get_instance().get(_KEY_IN), _VALUE)

    def test_it_doesnt_write_to_cache_when_disabled(self):
        _remove_temp_file()
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: "0"}):
            _get_instance()[_KEY_IN] = _VALUE
        self.assertFalse(os.path.isfile(TemporaryCache._TEMP_FILE_NAME))

    def test_it_doesnt_read_cache_when_disabled(self):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, int(time())]}})
        with patch.dict("os.environ", {TemporaryCache._ENV_VAR_EXPIRY: "0"}):
            self.assertIsNone(_get_instance().get(_KEY_IN))

    @parameterized.expand(_WRONG_EXPIRY_VALUES, name_func=get_test_case_name_without_index)
    def test_it_ignores_invalid_expiry_cache_value_(self, _name, value):
        _create_temp_file({_PROJECT: {_KEY_OUT: [_VALUE, value]}})
        self.assertIsNone(_get_instance().get(_KEY_IN))

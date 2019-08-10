import os
from typing import Union, Dict, List
from unittest import TestCase

from parameterized import parameterized
from ujson import dumps, loads

from temporary_cache import TemporaryCache


_PROJECT = "radeklat/issue-watcher"
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
    class TestCache(TemporaryCache):
        pass

    return TestCache(_PROJECT)


class TempCache(TestCase):
    def test_it_can_read_from_a_file(self):
        _create_temp_file({_PROJECT: {"Test-1": _VALUE}})
        self.assertEqual(_get_instance()["1"], _VALUE)

    def test_it_can_write_into_a_file(self):
        _create_temp_file()
        _get_instance()["1"] = _VALUE
        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {"Test-1": _VALUE}})

    def test_it_raises_key_error_when_key_is_missing(self):
        _create_temp_file()
        with self.assertRaises(KeyError):
            _value = _get_instance()["1"]

    def test_it_ignores_non_json_file(self):
        _create_temp_file('asdjfkk{:}:""')
        _get_instance()["1"] = _VALUE
        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {"Test-1": _VALUE}})

    def test_it_ignores_json_file_without_top_level_dict(self):
        _create_temp_file([1, 2, 3, 4])
        _get_instance()["1"] = _VALUE
        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {"Test-1": _VALUE}})

    def test_it_ignores_missing_file(self):
        _remove_temp_file()

        with self.assertRaises(KeyError):
            _value = _get_instance()["1"]

    def test_it_separates_projects(self):
        _remove_temp_file()

        class TestCache(TemporaryCache):
            pass

        TestCache(_PROJECT)["1"] = _VALUE
        TestCache(_PROJECT + "x")["1"] = _VALUE

        self.assertDictEqual(
            loads(_read_temp_file()),
            {_PROJECT: {"Test-1": _VALUE}, _PROJECT + "x": {"Test-1": _VALUE}},
        )

    def test_it_uses_class_name_as_value_type(self):
        _remove_temp_file()

        class _SampleTestCache(TemporaryCache):
            pass

        _SampleTestCache(_PROJECT)["1"] = _VALUE

        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {"SampleTest-1": _VALUE}})

    def test_it_separates_value_types(self):
        _remove_temp_file()

        class TestCache(TemporaryCache):
            pass

        class TestingCache(TemporaryCache):
            pass

        TestCache(_PROJECT)["1"] = _VALUE
        TestingCache(_PROJECT)["1"] = _VALUE

        self.assertDictEqual(
            loads(_read_temp_file()), {_PROJECT: {"Test-1": _VALUE, "Testing-1": _VALUE}}
        )


class TempCacheValueType(TestCase):
    def setUp(self):
        _remove_temp_file()

    def test_it_strips_cache(self):
        class SampleTestCache(TemporaryCache):
            pass

        SampleTestCache(_PROJECT)["1"] = _VALUE

        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {"SampleTest-1": _VALUE}})

    def test_it_strips_underscores(self):
        class _SampleTest(TemporaryCache):
            pass

        _SampleTest(_PROJECT)["1"] = _VALUE

        self.assertDictEqual(loads(_read_temp_file()), {_PROJECT: {"SampleTest-1": _VALUE}})


class TempCacheGet(TestCase):
    def setUp(self):
        _create_temp_file({_PROJECT: {"Test-1": _VALUE}})

    def test_it_returns_value_if_exists(self):
        self.assertEqual(_get_instance().get("1"), _VALUE)

    def test_it_returns_none_by_default_when_key_is_missing(self):
        self.assertIsNone(_get_instance().get("2"))

    def test_it_returns_custom_default_value_when_key_is_missing(self):
        self.assertEqual(_get_instance().get("3", _VALUE), _VALUE)

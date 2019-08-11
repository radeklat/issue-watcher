from abc import ABC
from collections import defaultdict
from contextlib import contextmanager
from os.path import join
from tempfile import gettempdir
from typing import DefaultDict, Iterator

from ujson import dump, load


class TemporaryCache(ABC):
    _TEMP_FILE_NAME = join(gettempdir(), "issue-watcher-cache.json")

    def __init__(self, project_identifier: str):
        self._project_identifier = project_identifier
        self._value_type = self.__class__.__name__.replace("Cache", "").replace("_", "")

    @contextmanager
    def _session(self, save: bool) -> Iterator[DefaultDict]:
        try:
            with open(self._TEMP_FILE_NAME, "r") as temp_file:
                cache = load(temp_file)
            if not isinstance(cache, dict):
                raise ValueError("Cache must be a dict.")
            cache = defaultdict(dict, cache)
        except (FileNotFoundError, ValueError):
            cache = defaultdict(dict)

        try:
            yield cache
        finally:
            if save:
                with open(self._TEMP_FILE_NAME, "w") as temp_file:
                    dump(cache, temp_file)

    def __setitem__(self, key: str, value: str):
        with self._session(save=True) as cache:
            cache[self._project_identifier][f"{self._value_type}-{key}"] = value

    def __getitem__(self, key: str) -> str:
        with self._session(save=False) as cache:
            return cache[self._project_identifier][f"{self._value_type}-{key}"]

    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        with self._session(save=True) as cache:
            cache.clear()

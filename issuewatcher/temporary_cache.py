import os
import os.path
import time
import warnings
from collections import defaultdict
from contextlib import contextmanager
from tempfile import gettempdir
from typing import DefaultDict, Iterator, Union

from ujson import dump, load


class TemporaryCache:
    _TEMP_FILE_NAME = os.path.join(gettempdir(), "issue-watcher-cache.json")
    _ENV_VAR_EXPIRY = "CACHE_INVALIDATION_IN_SECONDS"
    _DEFAULT_EXPIRY = 3600

    def __init__(self, project_identifier: str):
        self._project_identifier = project_identifier

        try:
            self._expire_in_seconds = int(
                os.environ.get(self._ENV_VAR_EXPIRY, self._DEFAULT_EXPIRY)
            )
            if self._expire_in_seconds < 0:
                raise ValueError("Cache invalidation must be 0 or positive integer.")
        except ValueError:
            value = os.environ[self._ENV_VAR_EXPIRY]
            warnings.warn(
                "issuewatcher seems to be improperly configured. Expected "
                f"'{self._ENV_VAR_EXPIRY}' environment variable to be 0 or "
                f"positive integer. However, value of '{value}' was used "
                f"instead and will be ignored. Using default value of "
                f"'{self._DEFAULT_EXPIRY}'.",
                RuntimeWarning,
            )

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

    def __setitem__(self, key: Union[str, int], value: str):
        if self._expire_in_seconds:
            with self._session(save=True) as cache:
                cache[self._project_identifier][key] = [value, int(time.time())]

    def __getitem__(self, key: Union[str, int]) -> str:
        if not self._expire_in_seconds:
            raise KeyError("Cache is disabled.")

        with self._session(save=False) as cache:
            try:
                value, timestamp = cache[self._project_identifier][key]
                timestamp = int(timestamp)
            except ValueError:
                raise KeyError()

        if timestamp < time.time() - self._expire_in_seconds:
            raise KeyError()

        return value

    def get(self, key: Union[str, int], default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        with self._session(save=True) as cache:
            cache.clear()

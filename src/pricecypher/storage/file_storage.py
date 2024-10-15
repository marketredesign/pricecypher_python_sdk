from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC
from contextlib import contextmanager
from pathlib import Path
from typing import Type, Union, Optional

import pandas as pd
import pickle
import pyarrow as pa
import pyarrow.parquet as pq
import smart_open

from pricecypher.encoders import JsonSerializable, PriceCypherJsonEncoder
from pricecypher.dataclasses import HandlerSettings, Models
from pricecypher.dataclasses.settings.remote_storage_settings import RemoteStorageSettings
from pricecypher.exceptions import InvalidStateException
from pricecypher.storage.transport_params_factory import create_transport_params

p_has_url_proto = re.compile('(.+)://(.+)')


class FileStorage(ABC):
    _path_local: str
    _path_remote_base: str
    _path_remote_prefix: str
    _remote_storage_settings: RemoteStorageSettings

    def __init__(
            self,
            path_local: str,
            path_remote_base: str,
            path_remote_prefix: str,
            remote_storage_settings: RemoteStorageSettings = None,
    ) -> None:
        """Utility class to handle file storage operations, aiming to simplify dealing with remotely synced files.

        :param path_local: Path on local filesystem where artifacts should be stored. We assume these artifacts are
            eventually uploaded to a remote location.
        :param path_remote_base: Base path of the remote storage, e.g. an URI pointing to the root of an S3 bucket.
        :param path_remote_prefix: Location within / on top of `path_remote_base` where remote artifacts will end up.

        NB: Values should be such that a locally stored 'file' at `path_local / file` matches with a remote copy at
        `path_remote_base / path_remote_prefix / file`.
        """
        self._path_local = path_local
        self._path_remote_base = path_remote_base
        self._path_remote_prefix = path_remote_prefix
        self._remote_storage_settings = remote_storage_settings or RemoteStorageSettings()

    def get_path_local(self, filename: str) -> str:
        return os.path.join(self._path_local, filename)

    def get_path_remote(self, filename: str, full: bool = True) -> str:
        """Get path in remote storage where the given locally stored file will end up.
        :param filename: Name of the file.
        :param full: Whether the full remote path, so including `self._path_remote_base`, should be returned.
        :return: Path in remote storage. Either absolute (including 'base') or relative, depending on given `full`.
        """
        suffix = os.path.join(self._path_remote_prefix, filename)

        if not full:
            return suffix

        return os.path.join(self._path_remote_base, suffix)

    @classmethod
    def get_scheme(cls, uri_as_string) -> Optional[str]:
        uri = smart_open.parse_uri(uri_as_string)
        return uri.scheme if hasattr(uri, 'scheme') else 'file'

    def get_scheme_local(self, filename: str) -> str:
        return self.get_scheme(self.get_path_local(filename))

    def get_scheme_remote(self, filename: str) -> str:
        return self.get_scheme(self.get_path_remote(filename))

    @contextmanager
    def save(self, filename: str, mode: str = 'w') -> str:
        """Open a file handler context to a new file in local storage.
        NB: the locally saved file should be uploaded to the remote storage automatically / externally.

        :param filename: Name of the file to save.
        :param mode: (Optional) Mimicks the `mode` parameter of the built-in `open` function. Defaults to 'w'.

        See Also
        --------
        - `Standard library reference <https://docs.python.org/3.7/library/functions.html#open>`__
        - `smart_open README.rst <https://github.com/RaRe-Technologies/smart_open/blob/master/README.rst>`__

        """
        if not self._path_local:
            raise InvalidStateException("The `path_local_outputs` and `path_local_outputs` must be set to save files.")

        local = self.get_path_local(filename)
        scheme = self.get_scheme(local)
        transport_params = create_transport_params(self._remote_storage_settings, scheme)

        logging.info(f"Saving file, local path = '{local}', remote path = '{self.get_path_remote(filename)}'...")

        if scheme == 'file':
            logging.debug("Making non-existing directories on the path to parent of `file_path_local`...")
            Path(local).parent.mkdir(parents=True, exist_ok=True)

        with smart_open.open(local, mode, transport_params=transport_params) as file:
            yield file

    @contextmanager
    def load(self, path: Union[Path, str], mode: str = 'r') -> str:
        """Open a file handler context to the give (remote) file path.

        :param path: Either an absolute path to a (remote) file, or a relative path from the remote file store.
        :param mode: (Optional) Mimicks the `mode` parameter of the built-in `open` function. Defaults to 'r'.
        """
        scheme = self.get_scheme(path)

        if isinstance(path, Path):
            path = path.as_posix()

        if scheme == 'file' and not Path(path).is_absolute():
            path = self.get_path_remote(path)

        transport_params = create_transport_params(self._remote_storage_settings, scheme)

        logging.debug(f"Loading / opening (remote) file at path '{path}'...")

        with smart_open.open(path, mode, transport_params=transport_params) as file:
            yield file

    @classmethod
    def from_handler_settings(cls: Type[FileStorage], settings: HandlerSettings) -> FileStorage:
        return cls(
            path_local=settings.path_local_out,
            path_remote_base=settings.path_remote_out_base,
            path_remote_prefix=settings.path_remote_out_prefix,
            remote_storage_settings=settings.remote_storage_settings,
        )

    def read_df(self, path: str) -> pd.DataFrame:
        """Read a DataFrame pickle from the file at the given path.
        :param path: the path to read from.
        :return: the DataFrame.
        """
        with self.load(path, mode='rb') as f:
            return pd.read_pickle(f)

    def read_models(self, path: str) -> Models:
        """Read a Models pickle from the file at the given path.
        :param path: the path to read from.
        :return: the Models.
        """
        with self.load(path, mode='rb') as f:
            return pickle.load(f)

    def read_parquet(self, path: str) -> pa.Table:
        """Read a parquet file from the file at the given path.
        :param path: the path to read from.
        :return: the DataFrame.
        """
        with self.load(path, mode='rb') as f:
            return pq.read_table(f)

    def read_string(self, path: str) -> str:
        """Read the contents of a file at the given path as string.
        :param path: the path to read from.
        :return: the file contents.
        """
        with self.load(path, mode='r') as f:
            return f.read()

    def write_df(self, path: str, df: pd.DataFrame) -> str:
        """Write a DataFrame to a pickle.
        :param path: the path to write the pickle to.
        :param df: the DataFrame to store.
        :return: the remote storage path.
        """
        with self.save(path, mode='wb') as f:
            pd.to_pickle(df, f)
        return self.get_path_remote(path)

    def write_metadata(self, path: str, metadata: JsonSerializable) -> str:
        """Serializes metadata to JSON and stores in a file at the given path.
        :param path: the path to store the metadata to.
        :param metadata: should be serializable by PriceCypherJsonEncoder.
        :return: the remote storage path.
        """
        json_metadata = json.dumps(metadata, cls=PriceCypherJsonEncoder)
        return self.write_string(path, json_metadata)

    def write_models(self, path: str, models: Models) -> str:
        """Creates a pickle from Models and stores it at the given path.
        :param path: the path to store 'models' to.
        :param models: the Models to store.
        :return: the remote storage path.
        """
        with self.save(path, mode='wb') as f:
            pickle.dump(models, f)
        return self.get_path_remote(path)

    def write_parquet(self, path: str, table: pa.Table) -> str:
        """Write a parquet file.
        :param path: the path to write the parquet file to.
        :param table: the Table to store.
        :return: the remote storage path.
        """
        with self.save(path, mode='wb') as f:
            pq.write_table(table, f)
        return self.get_path_remote(path)

    def write_string(self, path: str, string: str) -> str:
        """Write a string to a file.
        :param path: the path to write the file to.
        :param string: the string to write to the file.
        :return: the remote storage path.
        """
        with self.save(path, mode='w') as f:
            f.write(string)
        return self.get_path_remote(path)

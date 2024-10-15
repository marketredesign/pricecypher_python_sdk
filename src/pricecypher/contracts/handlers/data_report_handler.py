from abc import abstractmethod
from typing import Any

import pandas as pd

from .base_handler import BaseHandler
from pricecypher.dataclasses import TestSuite
from pricecypher.enums import AccessTokenGrantType


class DataReportHandler(BaseHandler):
    """The abstract DataReportHandler class provides a base for storing a TestSuite report based on a pandas DataFrame.
    Extend this class and override the `process()` method when you want to receive a DataFrame and do data checks on
    it.
    The input DataFrame should be available as a pickle at the `path_in` location. The output TestSuite will be stored
    as a json file at the `path_metadata_out` location. For consistency the (unaltered) input DataFrame is stored at the
    `path_out` location as well.
    """

    def get_allowed_access_token_grant_types(self) -> set[AccessTokenGrantType]:
        return set()

    def get_config_dependencies(self) -> dict[str, list[str]]:
        return dict()

    def handle(self, user_input: dict[str, Any]) -> any:
        """Handle the given `user_input`.
        Needs a pandas DataFrame stored as a pickle at the `path_in` location. The output json will be stored at the
        `path_metadata_out` location. For consistency the (unaltered) input DataFrame is stored at `path_out` as well.

        :param user_input: requires `path_in`, `path_out` and `path_metadata_out`.
        :return: the remote storage path of the DataFrame.
        """
        input_df = self._file_storage.read_df(user_input.get('path_in'))
        self._file_storage.write_metadata(user_input.get('path_metadata_out'), self.process(input_df))
        return self._file_storage.write_df(user_input.get('path_out'), input_df)

    @abstractmethod
    def process(self, df: pd.DataFrame) -> list[TestSuite]:
        """Override to implement and run data checks on the input DataFrame.

        :param df: the input DataFrame.
        :return: the resulting TestSuite.
        """
        raise NotImplementedError

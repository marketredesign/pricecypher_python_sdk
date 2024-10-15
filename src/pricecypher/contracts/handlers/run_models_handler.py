from abc import abstractmethod
from typing import Any

import pandas as pd

from .base_handler import BaseHandler
from pricecypher.dataclasses import Models
from pricecypher.enums import AccessTokenGrantType


class RunModelsHandler(BaseHandler):
    """The abstract RunModelsHandler class provides a base for running trained models on a pandas DataFrame.
    Extend this class and override the `process()` method when you want to run your trained models on the DataFrame and
    add the results to it (as extra columns).
    The input Models should be available as a pickle at the 'path_models_in' location.
    The input DataFrame should be available as a pickle at the `path_in` location.
    The output DataFrame will be stored as a pickle at the `path_out` location.
    """

    def get_allowed_access_token_grant_types(self) -> set[AccessTokenGrantType]:
        return set()

    def get_config_dependencies(self) -> dict[str, list[str]]:
        return dict()

    def handle(self, user_input: dict[str, Any]) -> any:
        """Handle the given `user_input`.
        Needs a Models pickle stored at `path_models_in` and a pandas DataFrame stored as a pickle at `path_in`.
        The output pandas DataFrame will be stored as a pickle at the `path_out` location.

        :param user_input: requires `path_in`, `path_models_in`, and `path_out`.
        :return: the remote storage path.
        :raise RuntimeError: when the number of rows of the output is not equal to the input.
        """
        input_df = self._file_storage.read_df(user_input.get('path_in'))
        input_trained_models = self._file_storage.read_models(user_input.get('path_models_in'))
        num_rows_input = input_df.shape[0]
        output_df = self.process(input_trained_models, input_df)
        self._guard_num_rows(output_df, num_rows_input)
        return self._file_storage.write_df(user_input.get('path_out'), output_df)

    @abstractmethod
    def process(self, models: Models, df: pd.DataFrame) -> pd.DataFrame:
        """Override to implement and run one or more models on the input DataFrame.
        Add the results as one or more extra columns.
        The output DataFrame should have the same number of rows as the input DataFrame, unless explicitly overruled by
        overriding the `_guard_num_rows()` function.

        :param models: the Models.
        :param df: the input DataFrame.
        :return: the resulting DataFrame.
        """
        raise NotImplementedError

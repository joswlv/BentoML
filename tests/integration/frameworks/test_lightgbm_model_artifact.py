import lightgbm
import numpy as np
import pandas as pd
import pytest

from bentoml.lightgbm import LightGBMModel
from tests._internal.helpers import assert_have_file_extension


@pytest.fixture()
def get_model() -> "lightgbm.Booster":
    data = lightgbm.Dataset(np.array([[0]]), label=np.array([0]))
    return lightgbm.train({}, data, 100)


def test_lightgbm_save_load(get_model, tmpdir):
    test_df: pd.DataFrame = pd.DataFrame([[0]])
    LightGBMModel(get_model).save(tmpdir)
    assert_have_file_extension(tmpdir, ".txt")

    loaded_model: "lightgbm.Booster" = LightGBMModel.load(tmpdir)
    assert loaded_model.predict(test_df) == get_model.predict(test_df)

import math
import pandas as pd
from solution import add_row


def test_input_unchanged_and_index():
    df = pd.DataFrame({"a": [1, 2]}, index=[10, 20])
    out = add_row(df, {"a": 3})
    assert len(df) == 2 and list(df.index) == [10, 20]
    assert list(out.index) == [0, 1, 2]


def test_missing_column_nan():
    df = pd.DataFrame({"a": [1], "b": [2.0]})
    out = add_row(df, {"a": 5})
    assert math.isnan(out.iloc[-1]["b"])


def test_empty_frame():
    df = pd.DataFrame(columns=["a", "b"])
    out = add_row(df, {"a": 1, "b": 2})
    assert len(out) == 1 and out.iloc[0]["a"] == 1

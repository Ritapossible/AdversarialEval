import pandas as pd
from solution import add_row


def test_appends():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    out = add_row(df, {"a": 3, "b": "z"})
    assert len(out) == 3
    assert out.iloc[-1]["a"] == 3 and out.iloc[-1]["b"] == "z"

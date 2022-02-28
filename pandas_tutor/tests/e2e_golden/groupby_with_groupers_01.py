# https://github.com/SamLau95/pandas_tutor/issues/72
# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
import pandas as pd
import numpy as np
np.random.seed(0)

arrays = [
    ["bar", "bar", "baz", "baz", "foo", "foo", "qux", "qux"],
    ["one", "two", "one", "two", "one", "two", "one", "two"],
]
index = pd.MultiIndex.from_arrays(arrays, names=["first", "second"])

df = pd.DataFrame({"A": [1, 1, 1, 1, 2, 2, 3, 3], "B": np.arange(8)}, index=index)

df.groupby([pd.Grouper(level=1), "A"]).mean()

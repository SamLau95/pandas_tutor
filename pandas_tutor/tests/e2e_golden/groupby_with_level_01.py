# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
import pandas as pd
import numpy as np
np.random.seed(0)

df = pd.DataFrame(
    {
        "A": ["foo", "bar", "foo", "bar", "foo", "bar", "foo", "foo"],
        "B": ["one", "one", "two", "three", "two", "two", "one", "three"],
        "C": np.random.randn(8),
        "D": np.random.randn(8),
    }
)

df2 = df.set_index(["A", "B"])
df2.groupby(level=df2.index.names.difference(["B"])).mean()
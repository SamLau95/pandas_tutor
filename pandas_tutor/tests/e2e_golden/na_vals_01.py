# tests that all nullish values are serialized to JSON null
# adapted from https://pandas.pydata.org/docs/user_guide/missing_data.html
import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.DataFrame(
    np.random.randn(5, 3),
    index=["a", "c", "e", "f", "h"],
    columns=["one", "two", "three"],
)
df["four"] = "bar"
df["five"] = df["one"] > 0

df2 = df.copy()
df2["timestamp"] = pd.Timestamp("20120101")
df2.loc[["a", "c", "h"], ["one", "timestamp"]] = np.nan

# >>> df2
#         one       two     three four   five  timestamp
# a       NaN -0.282863 -1.509059  bar   True        NaT
# c       NaN  1.212112 -0.173215  bar  False        NaT
# e  0.119209 -1.044236 -0.861849  bar   True 2012-01-01
# f -2.104569 -0.494929  1.071804  bar  False 2012-01-01
# h       NaN -0.706771 -1.039575  bar   True        NaT

df2.sort_values('two')

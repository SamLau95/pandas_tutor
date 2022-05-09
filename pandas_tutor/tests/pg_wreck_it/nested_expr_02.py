# https://github.com/SamLau95/pandas_tutor/issues/32
# https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html
import pandas as pd
import numpy as np
np.random.seed(0) # uncomment if you want deterministic outputs
s = pd.Series([1, 3, 5, np.nan, 6, 8])
dates = pd.date_range("20130101", periods=6)
df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list("ABCD"))
df2 = df.copy()
df2["E"] = ["one", "one", "two", "three", "four", "three"]

df2[df2["E"].isin(["two", "four"])] # <-- is this an example of a nested expression?
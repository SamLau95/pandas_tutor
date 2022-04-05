# https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html
import pandas as pd
import numpy as np

np.random.seed(0)  # uncomment if you want deterministic outputs
s = pd.Series([1, 3, 5, np.nan, 6, 8])
dates = pd.date_range("20130101", periods=6)
df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list("ABCD"))

df.iloc[[1, 2, 4], [0, 2]]

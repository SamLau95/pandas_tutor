# https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html
import numpy as np
import pandas as pd

s = pd.Series([1, 3, 5, np.nan, 6, 8])
dates = pd.date_range("20130101", periods=6)
data = np.array([[ 1.14, -1.23,  0.4 , -0.68],
       [-0.87, -0.58, -0.31,  0.06],
       [-1.17,  0.9 ,  0.47, -1.54],
       [ 1.49,  1.9 ,  1.18, -0.18],
       [-1.07,  1.05, -0.4 ,  1.22],
       [ 0.21,  0.98,  0.36,  0.71]])

df = pd.DataFrame(data, index=dates, columns=list("ABCD"))

df["20130103":"20130105"]

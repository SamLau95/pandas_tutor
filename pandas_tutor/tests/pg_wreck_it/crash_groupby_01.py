# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
import pandas as pd
import numpy as np

lst = [1, 2, 3, 4, 5, 6] # <-- this was initially [1, 2, 3, 1, 2, 3] so i thought it was a duplicate index issue, but even with no duplicates it still crashes
s = pd.Series([1, 2, 3, 10, 20, 30], lst)
s.groupby(level=0)

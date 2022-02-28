# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
import pandas as pd
import numpy as np

df3 = pd.DataFrame({"X": ["A", "B", "A", "B"], "Y": [1, 4, 3, 2]})
df3.groupby(["X"]).get_group("A")
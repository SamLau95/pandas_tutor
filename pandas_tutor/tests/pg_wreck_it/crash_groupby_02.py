# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
import pandas as pd
df_list = [[1, 2, 3], [1, None, 4], [2, 1, 3], [1, 2, 2]]
df_dropna = pd.DataFrame(df_list, columns=["a", "b", "c"])
df_dropna.groupby(by=["b"])

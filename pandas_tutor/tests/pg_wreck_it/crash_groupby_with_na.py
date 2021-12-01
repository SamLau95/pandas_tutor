import pandas as pd

df_list = [[1, 2, None], [1, None, 4], [2, 1, 4], [100, 200, -5], [1, 2, None]]
x = pd.DataFrame(df_list, columns=["a", "b", "c"])

# test groupby with NaN rows in keys
x.groupby(by=["c"], dropna=False).sum()

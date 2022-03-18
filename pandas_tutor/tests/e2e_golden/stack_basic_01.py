# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.stack.html
import pandas as pd

df_single_level_cols = pd.DataFrame(
    [[0, 1], [2, 3]], index=["cat", "dog"], columns=["weight", "height"]
)

df_single_level_cols.stack()

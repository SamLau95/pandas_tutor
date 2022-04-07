# https://pandas.pydata.org/docs/reference/api/pandas.melt.html
import pandas as pd

df = pd.DataFrame({'A': {0: 'a', 1: 'b', 2: 'c'},
                   'B': {0: 1, 1: 3, 2: 5},
                   'C': {0: 2, 1: 4, 2: 6}})

df = df.rename_axis(columns='hello')

# tests that the column names are reused as the var_names by default
df.melt(id_vars='A', value_vars=['B', 'C'])

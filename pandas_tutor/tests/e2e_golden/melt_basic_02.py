# https://pandas.pydata.org/docs/reference/api/pandas.melt.html
import pandas as pd

df = pd.DataFrame({'A': {0: 'a', 1: 'b', 2: 'c'},
                   'B': {0: 1, 1: 3, 2: 5},
                   'C': {0: 2, 1: 4, 2: 6}})

# sets variable and value column names
df.melt(id_vars='A', value_vars=['C', 'B'],
        var_name='hello', value_name='world')

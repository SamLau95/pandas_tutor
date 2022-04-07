# https://pandas.pydata.org/docs/reference/api/pandas.melt.html
import pandas as pd

df = pd.DataFrame({'A': {0: 'a', 1: 'b', 2: 'c'},
                   'B': {0: 1, 1: 3, 2: 5},
                   'C': {0: 2, 1: 4, 2: 6}})

df.columns = [list('ABC'), list('DEF')]

# melt with a multi-index
df.melt(col_level=0, id_vars=['A'], value_vars=['B'])

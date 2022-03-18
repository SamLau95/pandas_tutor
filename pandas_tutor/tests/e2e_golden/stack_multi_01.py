# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.stack.html
import pandas as pd

multicol2 = pd.MultiIndex.from_tuples([('weight', 'kg'),
                                       ('height', 'm')])
df_multi_level_cols2 = pd.DataFrame([[1.0, 2.0], [3.0, 4.0]],
                                    index=['cat', 'dog'],
                                    columns=multicol2)

df_multi_level_cols2.stack([0, 1])
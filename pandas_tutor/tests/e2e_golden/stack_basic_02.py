# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.stack.html
import pandas as pd

multicol1 = pd.MultiIndex.from_tuples([('weight', 'kg'),
                                       ('weight', 'pounds')])
df_multi_level_cols1 = pd.DataFrame([[1, 2], [2, 4]],
                                    index=['cat', 'dog'],
                                    columns=multicol1)
# future_stack=True stops a FutureWarning because pandas will change the
# behavior of stack in v3.0.
df_multi_level_cols1.stack(future_stack=True)

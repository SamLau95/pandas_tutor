# https://github.com/SamLau95/pandas_tutor/issues/86
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.unstack.html

import pandas as pd
import numpy as np

index = pd.MultiIndex.from_tuples([('one', 'a'), ('one', 'b'),
                                   ('two', 'a'), ('two', 'b')])
s = pd.Series(np.arange(1.0, 5.0), index=index)
                
# test cases (uncomment one at a time)
# s.unstack(level=-1)
#s.unstack(level=0)

# we don't draw marks for the second unstack since it goes from
# dataframe -> series 
s.unstack(level=0).unstack()
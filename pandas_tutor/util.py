'''
utilities
'''

import typing as t
import numpy as np
import pandas as pd  # type: ignore


def indexes(main: t.Sequence, search: t.Sequence):
    '''returns indexes of search within main'''
    # https://stackoverflow.com/a/32191125
    sorter = np.argsort(main)
    return sorter[np.searchsorted(main, search, sorter=sorter)]


def mapt(fn, *args):
    "map(fn, *args) and return the result as a tuple."
    return tuple(map(fn, *args))


def matching_df_rows(df1: pd.DataFrame,
                     df2: pd.DataFrame) -> t.List[t.Tuple[int, int]]:
    return list(zip(df1.index, indexes(df1.index, df2.index)))

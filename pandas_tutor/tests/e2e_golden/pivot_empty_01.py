# https://pandas.pydata.org/pandas-docs/stable/user_guide/reshaping.html#reshaping-by-pivoting-dataframe-objects
import io
import warnings

import pandas as pd

# getting a weird warning that only shows up in unittest, so let's silence it
warnings.filterwarnings("ignore", category=DeprecationWarning)

csv = """
foo,bar,baz,zoo
one,A,1,x
one,B,2,y
one,C,3,z
two,A,4,q
two,B,5,w
two,C,6,t
"""

df = pd.read_csv(io.StringIO(csv))

# produces an empty dataframe with two row labels
df.pivot(index=["foo"], columns=["bar", "baz", "zoo"])

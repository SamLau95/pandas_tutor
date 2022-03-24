# https://pandas.pydata.org/pandas-docs/stable/user_guide/reshaping.html#reshaping-by-pivoting-dataframe-objects
import pandas as pd
import io

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

# result has multiindex for both rows and columns
df.pivot(index=["zoo", "foo"], columns="bar")

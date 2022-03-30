# https://pandas.pydata.org/pandas-docs/stable/user_guide/reshaping.html#reshaping-by-pivoting-dataframe-objects
import pandas as pd
import io

csv = """
A,B,C,D,E
foo,one,small,1,2
foo,one,large,2,4
foo,one,large,2,5
foo,two,small,3,5
foo,two,small,3,6
bar,one,large,4,6
bar,one,small,5,8
bar,two,small,6,9
bar,two,large,7,9
"""

df = pd.read_csv(io.StringIO(csv))

# D and E aggregated; implied by groupby-agg with mean
df.pivot_table(index="C")

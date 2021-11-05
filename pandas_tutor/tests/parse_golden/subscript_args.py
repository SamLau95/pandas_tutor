# Tests that parser can handle different types of args
# import pandas as pd

df.loc[:, 'Count']

df[['Name', 'Count']]
df[df.columns[:4]]

df[df['Count'] < 10000]

col = 'Name'
df[(df[col] > 10) | (df['Year'] >= 2020)]

mask = df['Count'] > 10
df[mask]

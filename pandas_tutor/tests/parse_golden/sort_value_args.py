# Tests that parser can handle different types of args
# import pandas as pd

# df.loc[:, 'Count']
# df[df['Count'] < 10000]
df.sort_values('Name')

cols = ['size', 'breed']
df.sort_values(cols)

df.sort_values(by=['entry_id'], ascending=False)

df.sort_values(axis=1, by='Name')
# df.groupby('Name').mean()
# df.rename(columns={'Name': 'n'})

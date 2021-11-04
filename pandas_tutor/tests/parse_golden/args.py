# Tests that parser can handle different types of args
df.loc[:, 'Count']
df[df['Count'] < 10000]
df.sort_values('Name')
df.groupby('Name').mean()
df.rename(columns={'Name': 'n'})

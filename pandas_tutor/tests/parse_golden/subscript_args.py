# Tests that parser can handle different types of susbcript args
df.loc[:, 'Count']

df[['Name', 'Count']]
df[df.columns[:4]]

df[df['Count'] < 10000]

col = 'Name'
df[(df[col] > 10) | (df['Year'] >= 2020)]

mask = df['Count'] > 10
df[mask]

(df
 .iloc[2:5]
 .loc[:, df['tricky'] == 'to parse']
)

(df
 [2:5]
 [df['also'] == 'tricky']
)

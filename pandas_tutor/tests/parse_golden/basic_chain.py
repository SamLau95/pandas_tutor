(df
 .sort_values('Name')
 .groupby('Sex')
 .loc[:, 'Count']
 .mean()
)
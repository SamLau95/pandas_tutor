(df
 .sort_values('Name')
 .loc[:, 'Count']
)
(df
 .sort_values('Name')
 .groupby('Sex')
 ['Count']
 .mean()
)
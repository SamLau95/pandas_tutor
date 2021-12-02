# Tests that parser can handle nested function calls and slices
df.assign(rando=np.random.randn(12))

df2[df2["E"].isin(["two", "four"])]

df.loc[df['first_name'].isin(['France', 'Tyisha', 'Eric'])]

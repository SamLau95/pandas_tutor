# test that last expr is parsed into chain even if it's an assignmment
grouped = df.groupby("class")

# test for multiple assignments
grouped = test = df.groupby("class")

# we don't parse annotated assignments
grouped: pd.DataFrame = df.groupby("class")

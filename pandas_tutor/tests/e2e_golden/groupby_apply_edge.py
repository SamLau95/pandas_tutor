import pandas as pd

# when after index look like positional index, but it is actually group names.
# Use this test case to make sure we are not providing the wrong information
# TODO: rewrite the golden file once groupers and custom function groupby are
# implemented
data = {"Group": ["A", "B", "C", "D", "E"], "Value": [4, 3, 2, 1, 0]}

# Creating DataFrame
df = pd.DataFrame(data)


def single_group(value):
    return value + 1


df.groupby(single_group).apply(lambda x: x.iloc[0])

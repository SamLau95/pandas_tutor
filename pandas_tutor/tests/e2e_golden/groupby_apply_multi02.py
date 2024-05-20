import pandas as pd

data = {
    "Category": ["A", "A", "B", "B", "A", "B", "A", "B"],
    "Subcategory": ["X", "Y", "X", "Y", "X", "X", "Y", "Y"],
    "Value1": [10, 20, 30, 40, 50, 60, 70, 80],
    "Value2": [100, 200, 300, 400, 500, 600, 700, 800],
}

df = pd.DataFrame(data)

df.groupby(["Category", "Subcategory"]).apply(lambda x: x.mean())

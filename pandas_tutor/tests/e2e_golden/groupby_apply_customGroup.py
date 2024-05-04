import pandas as pd

# Create a sample DataFrame
data = {
    "Category": ["A", "B", "A", "B", "A", "B"],
    "Value": [10, 20, 15, 25, 12, 18],
}
df = pd.DataFrame(data)


def even_odd(value):
    if value % 2 == 0:
        return "Even"
    else:
        return "Odd"


df.groupby(even_odd).apply(lambda x: x["Value"].mean())

import numpy as np
import pandas as pd

dates = pd.date_range("20130101", periods=6)

df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list("ABCD"))

df2 = df.copy()

# should NOT be parsed as a subscript
df2["E"] = ["one", "one", "two", "three", "four", "three"]

import pandas as pd
import numpy as np
import io

# test case for getCall

num_rows = 500  # 1 million rows
num_columns = 10  # 50 columns

# Create a DataFrame with random floats
testing = pd.DataFrame(
    np.random.rand(num_rows, num_columns),
    columns=[f"col{i}" for i in range(num_columns)],
)

print(testing)
testing.sort_values("col2")

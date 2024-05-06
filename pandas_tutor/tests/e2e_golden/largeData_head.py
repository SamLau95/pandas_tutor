import pandas as pd
import numpy as np
import io

num_rows = 500
num_columns = 500

testing = pd.DataFrame(
    np.random.rand(num_rows, num_columns),
    columns=[f"col{i}" for i in range(num_columns)],
)

testing.head()

import pandas as pd
import numpy as np

# this uses about 3 MB
big = pd.DataFrame({'numbers': np.arange(400_000)})

# but we sample it to make it smaller
big = big.sample(n=100, random_state=42)

big.head()

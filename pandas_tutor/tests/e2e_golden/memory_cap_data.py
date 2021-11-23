import pandas as pd
import numpy as np

# this uses about 1.5 MB
big = pd.DataFrame({'numbers': np.arange(200_000)})

big.head()

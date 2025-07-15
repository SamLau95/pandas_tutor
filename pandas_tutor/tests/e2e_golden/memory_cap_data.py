import numpy as np
import pandas as pd

# this uses about 1.5 MB and should be okay
big = pd.DataFrame({'numbers': np.arange(200_000)})

big.head()

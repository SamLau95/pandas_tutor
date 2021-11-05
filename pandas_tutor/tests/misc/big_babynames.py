# do not run this in the normal test suite!
# was just trying to give pg a very large JSON for his backend

import pandas as pd
from pathlib import Path

baby = Path('datasets/babynames.csv').resolve()

df = pd.read_csv(baby)

df.head(5)

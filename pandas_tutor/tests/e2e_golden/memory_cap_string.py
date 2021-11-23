import pandas as pd

# this uses about 2.5 MB
big = pd.DataFrame({'text': ['hello world' * 120_000]})

big.head()

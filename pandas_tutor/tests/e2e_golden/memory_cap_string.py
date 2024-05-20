import pandas as pd

# this uses about 250 MB
big = pd.DataFrame({"text": ["hello world" * 12_000_000]})

big.head()

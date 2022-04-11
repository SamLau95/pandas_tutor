import pandas as pd
import io

csv = """
Name,Sex,Count,Year
Noah,M,18252,2020
Julius,M,960,2020
Karen,M,6,2020
Karen,F,325,2020
Noah,F,305,2020
"""

csv2 = """
nyt_name,category
Karen,boomer
Julius,mythology
Freya,mythology
"""

baby = pd.read_csv(io.StringIO(csv))
nyt = pd.read_csv(io.StringIO(csv2))

baby2 = baby.set_index("Name")

# when right doesn't use index, we can get duplicate index vals, so we don't
# handle
baby2.merge(nyt, left_index=True, right_on="nyt_name")

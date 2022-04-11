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
Julius,test
Julius,test2
Karen,boomer2
"""

baby = pd.read_csv(io.StringIO(csv))
nyt = pd.read_csv(io.StringIO(csv2))

nyt2 = nyt.rename(columns={"nyt_name": "Name"})

# Julius and Karen appear multiple times in both lhs and lhs2
baby.merge(nyt2, on="Name")

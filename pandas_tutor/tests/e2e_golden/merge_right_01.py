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

baby.merge(nyt, left_on="Name", right_on="nyt_name", how="right")

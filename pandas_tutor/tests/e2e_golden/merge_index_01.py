import pandas as pd
import io

csv = """
Name,Sex,Count,Year
Noah,M,18252,2020
Julius,M,960,2020
Karen,M,6,2020
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
nyt2 = nyt.set_index("nyt_name")

# tests index args
baby2.merge(nyt2, left_index=True, right_index=True)

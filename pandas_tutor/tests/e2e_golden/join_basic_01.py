import pandas as pd
import io

csv = """
Name,Sex,Count,Year
Noah,M,18252,2020
Julius,M,960,2020
Karen,F,325,2020
"""

csv2 = """
nyt_name,category
Karen,boomer
Julius,mythology
Freya,mythology
"""

baby = pd.read_csv(io.StringIO(csv)).set_index("Name")
nyt = pd.read_csv(io.StringIO(csv2)).set_index("nyt_name")

# join is like merge() except that by default it joins on the index and uses a
# left join.
baby.join(nyt)

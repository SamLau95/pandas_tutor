import pandas as pd
import io

csv = """
Name,Sex,Count,Year
Noah,M,18252,2020
Julius,M,960,2020
Karen,M,6,2020
Noah,F,305,2020
"""

baby = pd.read_csv(io.StringIO(csv)).set_index("Name")

baby.merge(baby)

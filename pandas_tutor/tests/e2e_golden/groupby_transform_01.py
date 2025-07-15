import io

import pandas as pd

csv = """
breed,type,longevity,size
Labrador,sporting,12.04,medium
German,herding,9.73,large
Beagle,hound,12.3,small
Golden,sporting,12.04,medium
Yorkshire,toy,12.6,small
Bulldog,non-sporting,6.29,medium
Boxer,working,8.81,medium
Poodle,non-sporting,11.95,medium
"""

dogs = pd.read_csv(io.StringIO(csv))

dogs.groupby("size")[['longevity']].transform(lambda s: s.mean())

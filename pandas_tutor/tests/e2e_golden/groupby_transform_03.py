import pandas as pd
import io

csv = """
breed,type,longevity,size,temp
Labrador,sporting,12.04,medium,1
German,herding,9.73,large,2
Beagle,hound,12.3,small,3
Golden,sporting,12.04,medium,4
Yorkshire,toy,12.6,small,5
Bulldog,non-sporting,6.29,medium,6
Boxer,working,8.81,medium,7
Poodle,non-sporting,11.95,medium,8
"""

dogs = pd.read_csv(io.StringIO(csv))

dogs.groupby("size")[["longevity", "temp"]].transform(lambda s: s.mean())

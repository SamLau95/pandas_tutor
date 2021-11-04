# Common point of confusion: difference between loc and iloc
#
# Compare loc_vs_iloc_01.py and loc_vs_iloc_02.py

import pandas as pd
import io

csv = '''
breed,grooming,food_cost,kids,size
Labrador Retriever,weekly,466.0,high,medium
German Shepherd,weekly,466.0,medium,large
Beagle,daily,324.0,high,small
Golden Retriever,weekly,466.0,high,medium
Yorkshire Terrier,daily,324.0,low,small
Bulldog,weekly,466.0,medium,medium
Boxer,weekly,466.0,high,medium
'''

dogs = pd.read_csv(io.StringIO(csv))

# These return different tables!
# dogs.sort_values('kids').iloc[0:6]
dogs.sort_values('kids').loc[0:6]

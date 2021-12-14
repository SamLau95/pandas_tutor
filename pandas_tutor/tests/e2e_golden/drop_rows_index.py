import pandas as pd
import io

csv = '''
breed,type,longevity,size
Labrador Retriever,sporting,12.04,medium
German Shepherd,herding,9.73,large
Beagle,hound,12.3,small
Golden,sporting,12.04,medium
Yorkshire,toy,12.6,small
Bulldog,non-sporting,6.29,medium
'''

dogs = (pd.read_csv(io.StringIO(csv))
  [['breed', 'type', 'longevity']]
)

dogs.drop(index=1, axis=1)
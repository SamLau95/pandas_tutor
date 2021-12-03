import pandas as pd
import io

csv = '''
breed,type,price,longevity,size
Labrador Retriever,sporting,810.0,12.04,medium
German Shepherd,herding,820.0,9.73,large
Beagle,hound,288.0,12.3,small
'''

dogs = pd.read_csv(io.StringIO(csv)).set_index('breed')

(dogs
 .drop(['Labrador Retriever', 'Beagle'])
)

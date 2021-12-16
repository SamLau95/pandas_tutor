import pandas as pd
import io

csv = '''
breed,type,longevity,size,weight
German Shepherd,herding,9.73,large,
Beagle,hound,12.3,small,
Yorkshire Terrier,toy,12.6,small,5.5
Golden Retriever,sporting,12.04,medium,60.0
Bulldog,non-sporting,6.29,medium,45.0
Labrador Retriever,sporting,12.04,medium,67.5
Boxer,working,8.81,medium,
Poodle,non-sporting,11.95,medium,
Dachshund,hound,12.63,small,24.0
Rottweiler,working,9.11,large,
Boston Terrier,non-sporting,10.92,medium,
Shih Tzu,toy,13.2,small,12.5
Miniature Schnauzer,terrier,11.81,small,15.5
Doberman Pinscher,working,10.33,large,
Chihuahua,toy,16.5,small,5.5
Siberian Husky,working,12.58,medium,47.5
Pomeranian,toy,9.67,small,5.0
French Bulldog,non-sporting,9.0,medium,27.0
Great Dane,working,6.96,large,
Shetland Sheepdog,herding,12.53,small,22.0
Cavalier King Charles Spaniel,toy,11.29,small,15.5
German Shorthaired Pointer,sporting,11.46,large,62.5
Maltese,toy,12.25,small,5.0
'''

dogs = pd.read_csv(io.StringIO(csv))

(dogs
 .groupby('type').plot() # <-- crashes when i try to do a plot() here
)

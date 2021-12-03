import pandas as pd
import io

csv = '''
breed,group,price,longevity,size
Labrador Retriever,sporting,810.0,12.04,medium
German Shepherd,herding,820.0,9.73,large
Beagle,hound,288.0,12.3,small
Golden Retriever,sporting,958.0,12.04,medium
Yorkshire Terrier,toy,1057.0,12.6,small
Bulldog,non-sporting,2680.0,6.29,medium
Boxer,working,700.0,8.81,medium
Poodle,non-sporting,900.0,11.95,medium
Dachshund,hound,423.0,12.63,small
Rottweiler,working,1118.0,9.11,large
Shih Tzu,toy,583.0,13.2,small
Miniature Schnauzer,terrier,715.0,11.81,small
Doberman Pinscher,working,790.0,10.33,large
Chihuahua,toy,588.0,16.5,small
German Shorthaired Pointer,sporting,545.0,11.46,large
Siberian Husky,working,650.0,12.58,medium
Pomeranian,toy,670.0,9.67,small
French Bulldog,non-sporting,1900.0,9.0,medium
Great Dane,working,1040.0,6.96,large
Shetland Sheepdog,herding,465.0,12.53,small
Cavalier King Charles Spaniel,toy,1017.0,11.29,small
Boston Terrier,non-sporting,690.0,10.92,medium
Maltese,toy,650.0,12.25,small
Australian Shepherd,herding,565.0,12.28,medium
Pembroke Welsh Corgi,herding,587.0,12.25,small
Pug,toy,469.0,11.0,medium
Cocker Spaniel,sporting,465.0,12.5,small
Mastiff,working,900.0,6.5,large
English Springer Spaniel,sporting,615.0,12.54,medium
Brittany,sporting,618.0,12.92,medium
Bernese Mountain Dog,working,1320.0,7.56,large
West Highland White Terrier,terrier,538.0,12.8,small
Papillon,toy,740.0,13.0,small
Bichon Frise,non-sporting,693.0,12.21,small
Bullmastiff,working,980.0,7.57,large
Basset Hound,hound,490.0,11.43,small
Newfoundland,working,1178.0,9.32,large
Rhodesian Ridgeback,hound,995.0,9.1,large
Border Collie,herding,623.0,12.52,medium
Chesapeake Bay Retriever,sporting,522.0,9.48,large
'''

dogs = pd.read_csv(io.StringIO(csv))

(dogs[dogs['size'] == 'small']
 .sort_values('group')
 .groupby('group').median()
)
import pandas as pd
import io

csv = """
breed,size,kids,longevity,price
Labrador Retriever,medium,high,12.04,810.0
Beagle,small,high,12.3,288.0
Golden Retriever,medium,high,12.04,958.0
Yorkshire Terrier,small,low,12.6,1057.0
Boxer,medium,high,8.81,700.0
Labrador Retriever,medium,high,12.04,810.0
Beagle,small,high,12.3,288.0
Golden Retriever,medium,high,12.04,958.0
Yorkshire Terrier,small,low,12.6,1057.0
Boxer,medium,high,8.81,700.0
Labrador Retriever,medium,high,12.04,810.0
Beagle,small,high,12.3,288.0
Golden Retriever,medium,high,12.04,958.0
Yorkshire Terrier,small,low,12.6,1057.0
Boxer,medium,high,8.81,700.0
Labrador Retriever,medium,high,12.04,810.0
Beagle,small,high,12.3,288.0
Golden Retriever,medium,high,12.04,958.0
Yorkshire Terrier,small,low,12.6,1057.0
Boxer,medium,high,8.81,700.0
Labrador Retriever,medium,high,12.04,810.0
Beagle,small,high,12.3,288.0
Golden Retriever,medium,high,12.04,958.0
Yorkshire Terrier,small,low,12.6,1057.0
Boxer,medium,high,8.81,700.0
Labrador Retriever,medium,high,12.04,810.0
Beagle,small,high,12.3,288.0
Golden Retriever,medium,high,12.04,958.0
Yorkshire Terrier,small,low,12.6,1057.0
Boxer,medium,high,8.81,700.0
"""
dogs = pd.read_csv(io.StringIO(csv))
# dogs = (dogs.groupby(['size', 'kids'])
#         [['longevity', 'price']]
#         .mean()
#         .reset_index())
# dogs.pivot(index='size', columns='kids')
dogs.groupby(["size", "kids"])[["longevity", "price"]].mean()

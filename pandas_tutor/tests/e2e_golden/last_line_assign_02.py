import pandas as pd
import io

csv = """
breed,grooming,food_cost,kids,size
Labrador Retriever,weekly,466.0,high,medium
German Shepherd,weekly,466.0,medium,large
Beagle,daily,324.0,high,small
Golden Retriever,weekly,466.0,high,medium
Yorkshire Terrier,daily,324.0,low,small
Bulldog,weekly,466.0,medium,medium
Boxer,weekly,466.0,high,medium
"""

dogs = pd.read_csv(io.StringIO(csv))

# tests that assignment chain on the last line is visualized
dogs = dogs.head(5).sort_values("breed").query("food_cost > 400")

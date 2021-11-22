# tests that fragments point to the right parts of the code

import pandas as pd
import io
csv = "breed,grooming,food_cost,kids,size"
dogs = pd.read_csv(io.StringIO(csv))

(    dogs  ["breed"] # <-- look at leading spaces here
 .apply(len) # another comment test
   .rename('test'   )       # test
)

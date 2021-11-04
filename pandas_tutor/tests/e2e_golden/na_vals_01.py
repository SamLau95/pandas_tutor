import pandas as pd
import numpy as np

df = pd.DataFrame([('Liam', 2020), (np.nan, 2020), ('Sophia', 2020),
                   ('Amelia', None)],
                  columns=['Name', 'Year'])

df.sort_values('Name')

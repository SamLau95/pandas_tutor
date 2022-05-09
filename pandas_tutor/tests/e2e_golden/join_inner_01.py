import pandas as pd
import io

building_records_1844 = pd.read_csv(io.StringIO('''
building,location,established
Grande Hotel,4-5,1831
Jone's Farm,1-2,1842
Public Library,6-4,1836
Marietta House,1-7,1823
''')).set_index(['building', 'location'])

building_records_2020 = pd.read_csv(io.StringIO('''
building,location,established
Sam's Bakery,5-1,1962
Grande Hotel,4-5,1830
Public Library,6-4,1835
Mayberry's Factory,3-2,1924
''')).set_index(['building', 'location'])

building_records_1844.join(
    building_records_2020,
    how='inner',
    rsuffix='_2000',
)
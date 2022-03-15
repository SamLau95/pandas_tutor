import pandas as pd
import io

csv = '''
Name,Sex,Count,Year
Liam,M,19659,2020
Noah,M,18252,2020
Oliver,M,14147,2020
Emma,F,15581,2020
Ava,F,13084,2020
Charlotte,F,13003,2020
Liam,M,20555,2019
Noah,M,19097,2019
Oliver,M,13929,2019
Emma,F,17155,2019
Ava,F,14474,2019
Sophia,F,13753,2019
'''

df = pd.read_csv(io.StringIO(csv))
counts = (
    df.groupby(['Year', 'Sex'])
    [['Count']]
    .max()
)

counts.unstack()

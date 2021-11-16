import pandas as pd
import io

csv = '''
date,id,pm25aqs,pm25pa
2018-11-01,CA1,9.4,9.46
2018-11-04,CA1,11.4,17.24
2018-11-03,CA2,5.67,7.43
2018-11-04,CA2,3.46,5.36
2018-12-01,CA1,6.4,9.28
2018-12-01,CA2,4.12,8.02
2018-12-02,CA2,2.38,4.03
2018-12-03,CA2,6.79,11.96
'''

pm = pd.read_csv(io.StringIO(csv))

months = pm['date'].str[5:7]

pm.groupby(months).mean()
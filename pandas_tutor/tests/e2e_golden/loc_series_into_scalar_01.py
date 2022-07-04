import pandas as pd
import io

csv = """
Player,Position,Team,Salary
Stephen Curry,PG,Golden State Warriors,45780966
Russell Westbrook,PG,Los Angeles Lakers,44211146
James Harden,PG,Brooklyn Nets,43848000
LeBron James,SF,Los Angeles Lakers,41180544
Kevin Durant,PF,Brooklyn Nets,40918900
"""

df = pd.read_csv(io.StringIO(csv)).set_index('Player')

series = df['Salary']
series.loc['Stephen Curry']

# tests that both Count and Sex appear in the output JSON
import pandas as pd

df = pd.DataFrame([('Liam', 'M', 19659, 2020), ('Noah', 'M', 18252, 2020),
                   ('Oliver', 'M', 14147, 2020), ('Elijah', 'M', 13034, 2020),
                   ('William', 'M', 12541, 2020), ('Emma', 'F', 15581, 2020),
                   ('Ava', 'F', 13084, 2020), ('Charlotte', 'F', 13003, 2020),
                   ('Sophia', 'F', 12976, 2020), ('Amelia', 'F', 12704, 2020)],
                  columns=['Name', 'Sex', 'Count', 'Year'])

df[(df['Count'] > 14000) & (df['Sex'] == 'F')]

#!/usr/bin/env python
# coding: utf-8

# In[106]:


# Reference: https://jupyterbook.org/interactive/hiding.html
# Use {hide, remove}-{input, output, cell} tags to hiding content

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
get_ipython().run_line_magic('matplotlib', 'inline')
import ipywidgets as widgets
from ipywidgets import interact, interactive, fixed, interact_manual
from IPython.display import display

sns.set()
sns.set_context('talk')
np.set_printoptions(threshold=20, precision=2, suppress=True)
pd.set_option('display.max_rows', 7)
pd.set_option('display.max_columns', 8)
pd.set_option('precision', 2)
# This option stops scientific notation for pandas
# pd.set_option('display.float_format', '{:.2f}'.format)

def display_df(df, rows=pd.options.display.max_rows,
               cols=pd.options.display.max_columns):
    with pd.option_context('display.max_rows', rows,
                           'display.max_columns', cols):
        display(df)


# # Transforming
# 
# Data scientists transform dataframe columns when they need to change each value
# in a feature in the same way. For example, if a feature contains heights of
# people in feet, a data scientist might want to transform the heights to
# centimeters. In this section, we'll introduce *apply*, an operation that
# transforms columns of data using a user-defined function.

# In[107]:


baby = pd.read_csv('babynames.csv')
baby


# In the baby names New York Times article {cite}`williamsLilith2021`, Pamela
# mentions that names starting with the letter "L" and "K" became popular
# after 2000. On the other hand, names starting with the letter "J" peaked in
# popularity in the 1970s and 1980s and have dropped off in popularity since. We
# can verify these claims using the `baby` dataset.
# 
# We approach this problem using the following steps:
# 
# 1. Transform the `Name` column into a new column that contains the first
#    letters of each value in `Name`.
# 2. Group the dataframe by the first letter and year.
# 3. Aggregate the name counts by summing.
# 
# To complete the first step, we'll *apply* a function to the `Name` column. 

# ## Apply 
# 
# `pd.Series` objects contain an `.apply()` method that takes in a function and
# applies it to each value in the series. For instance, to find the lengths of
# each name, we apply the `len` function.

# In[109]:


names = baby['Name']
names.apply(len)


# To extract the first letter of each name, define a custom function and pass it
# into `.apply()`.

# In[112]:


# The argument to the function is an individual value in the series. 
def first_letter(string):
    return string[0]

names.apply(first_letter)


# Using `.apply()` is similar to using a `for` loop. The code above is roughly
# equivalent to writing:
# 
# ```python
# result = []
# for name in names:
#     result.append(first_letter(name))
# ```

# Now, we can assign the first letters to a new column in the dataframe:

# In[118]:


letters = baby.assign(Firsts=names.apply(first_letter))
letters


# :::{note}
# 
# To create a new column in a dataframe, you might also encounter this syntax:
# 
# ```python
# baby['Firsts'] = names.apply(first_letter)
# ```
# 
# This mutates the `baby` table by adding a new column called `Firsts`. In the
# code above, we use `.assign()` which doesn't mutate the `baby` table itself; it
# creates a new dataframe instead. Mutating dataframes isn't wrong but can be a
# common source of bugs. Because of this, we'll mostly use `.assign()` in this
# book. 
# 
# :::

# ## Example: Popularity of "L" Names

# Now, we can use the `letters` dataframe to see the popularity of first letters
# over time.

# In[121]:


letter_counts = (letters
 .groupby(['Firsts', 'Year'])
 ['Count']
 .sum()
 .reset_index()
)
letter_counts


# In[125]:


(letter_counts
 .loc[letter_counts['Firsts'] == 'L']
 .plot('Year', 'Count')
)
plt.title('Popularity of "L" names');


# The plot shows that "L" names were popular in the 1960s, dipped in the decades
# after, but have indeed resurged in popularity after 2000. 
# 
# What about "J" names?

# In[126]:


(letter_counts
 .loc[letter_counts['Firsts'] == 'J']
 .plot('Year', 'Count')
)
plt.title('Popularity of "J" names');


# The NYT article says that "J" names were popular in the 1970s and 80s. The plot
# agrees, and also shows that they have become less popular after 2000.

# ## The Price of Apply
# 
# The power of `.apply()` is its flexibility---you can call it with any function
# that takes in a single data value and outputs a single data value.
# 
# Its flexibility has a price, though. Using `.apply()` can be slow, since
# `pandas` can't optimize arbitrary functions. For example, using `.apply()` for
# numeric calculations is much slower than using vectorized operations directly
# on `pd.Series` objects:

# In[140]:


get_ipython().run_cell_magic('timeit', '', "\n# Calculate the decade using vectorized operators\nbaby['Year'] // 10 * 10")


# In[141]:


get_ipython().run_cell_magic('timeit', '', "\ndef decade(yr):\n    return yr // 10 * 10\n\n# Calculate the decade using apply\nbaby['Year'].apply(decade)")


# The version using `.apply()` is more than 30 times slower! For numeric
# operations in particular, we recommend operating on `pd.Series` objects
# directly.

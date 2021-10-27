#!/usr/bin/env python
# coding: utf-8

# In[2]:


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


# # Aggregating
# 
# This section introduces operations for aggregating rows in a dataframe. Data
# scientists aggregate rows together to make summaries of data. For instance, a
# dataset containing daily sales can be aggregated to show monthly sales instead.
# Specifically, we'll introduce *grouping* and *pivoting*, two common operations
# for aggregating data.
# 
# We'll work with the baby names data, as introduced in the previous section:

# In[3]:


baby = pd.read_csv('babynames.csv')
baby


# ## Basic Group-Aggregate

# Let's say we want to find out the total number of babies born as recorded in
# this data. This is simply the sum of the `Count` column:

# In[4]:


baby['Count'].sum()


# Summing up the name counts is one simple way to aggregate the data---it
# combines data from multiple rows.

# But let's say we instead want to answer a more interesting question: are U.S.
# births trending upwards over time? To answer this question, we can sum the
# `Count` column within each year rather than taking the sum over the entire
# dataset. In other words, we split the data into groups based on `Year`,
# then sum up the `Count` values within each group.
# 
# ```{figure} figures/groupby-births.svg
# ---
# name: groupby-births
# alt: groupby-births
# ---
# A depiction of grouping then aggregating for example data.
# ```

# We call this operation **grouping** followed by **aggregating**. In `pandas`,
# we write: 

# In[5]:


baby.groupby('Year')['Count'].sum()


# Notice that the code is nearly the same as the non-grouped version, except that
# it starts with a call to `.groupby('Year')`.
# 
# The result is a `pd.Series` with the total babies born for each year in the
# data. Notice that the index of this series contains the unique `Year` values.
# Now we can plot the counts over time:

# In[6]:


counts_by_year = baby.groupby('Year')['Count'].sum()
counts_by_year.plot();


# What do we see in this plot? First, we notice that there seem to be
# suspiciously few babies born before 1920. One likely explanation is that the
# Social Security Administration was created in 1935, so its data for prior
# births could be less complete.
# 
# We also notice the dip when World War II began in 1939, and the
# post-war Baby Boomer era from 1946-1964.

# Here's the basic recipe for grouping in `pandas`:
# 
# ```python
# (baby                # the dataframe
#  .groupby('Year')    # column(s) to group
#  ['Count']           # column(s) to aggregate
#  .sum()              # how to aggregate
# )
# ```

# ## Grouping on Multiple Columns
# 
# We pass multiple columns into `.groupby` as a list to group by multiple
# columns at once. This is useful when we need to further subdivide our groups.
# For example, we can group by both year and sex to see how many male and female
# babies were born over time.

# In[7]:


counts_by_year_and_sex = (baby
 .groupby(['Year', 'Sex']) # Arg to groupby is a list of column names
 ['Count']
 .sum()
)
counts_by_year_and_sex 


# Notice how the code closely follows the grouping recipe.
# 
# The `counts_by_year_and_sex` series has what we call a multi-level index with
# two levels, one for each column that was grouped. It's a bit easier to see if
# we convert the series to a dataframe:

# In[8]:


# The result only has one column
counts_by_year_and_sex.to_frame()


# There are two levels to the index because we grouped by two columns. It can be
# a bit tricky to work with multilevel indices, so we can reset the index to go
# back to a dataframe with a single index.

# In[9]:


counts_by_year_and_sex.reset_index()


# ## Custom Aggregation Functions
# 
# After grouping, `pandas` gives us flexible ways to aggregate the data. So far,
# we've seen how to use `.sum()` after grouping:

# In[10]:


(baby
 .groupby('Year')
 ['Count']
 .sum() # aggregate by summing
)


# `pandas` also supplies other aggregation functions, like `.mean()`, `.size()`,
# and `.first()`. Here's the same grouping using `.max()`:

# In[19]:


(baby
 .groupby('Year')
 ['Count']
 .max() # aggregate by taking the max within each group
)


# But sometimes `pandas` doesn't have the exact aggregation function we want to
# use. In these cases, we can define and use a custom aggregation function.
# `pandas` lets us do this through `.agg(fn)`, where `fn` is a function that we
# define.
# 
# For instance, if we want to find the difference between the largest and
# smallest values within each group (the range of the data), we could first
# define a function called `data_range`, then pass that function into `.agg()`.

# In[20]:


# The input to this function is a pd.Series object containing a single column
# of data. It gets called once for each group.
def data_range(counts):
    return counts.max() - counts.min()

(baby
 .groupby('Year')
 ['Count']
 .agg(data_range) # aggregate using custom function
)


# ## Example: Have People Become More Creative With Baby Names?
# 
# Have people become more creative with baby names over time? One way to measure
# this is to see whether the number of *unique* baby names per year has increased
# over time.

# We start by defining a `count_unique` function that counts the number of
# unique values in a series. Then, we pass that function into `.agg()`.

# In[13]:


def count_unique(s):
    return len(s.unique())

unique_names_by_year = (baby
 .groupby('Year')
 ['Name']
 .agg(count_unique) # aggregate using the custom count_unique function
)
unique_names_by_year


# In[14]:


unique_names_by_year.plot();


# We see that the number of unique names has generally increased over time, even
# though the number of babies born has mostly stabilized since the 1960s.

# ## Pivoting
# 
# Pivoting is essentially a convenient way to arrange the results of a group and
# aggregation when grouping with two columns. Earlier in this section we grouped
# the baby names data by year and sex:

# In[15]:


counts_by_year_and_sex = (baby
 .groupby(['Year', 'Sex']) 
 ['Count']
 .sum()
)
counts_by_year_and_sex.to_frame()


# This produces a `pd.Series` with the counts. We can also imagine the same data
# with the `Sex` index level "pivoted" to the columns of a dataframe. It's easier
# to see with an example:

# In[16]:


mf_pivot = pd.pivot_table(
    baby,
    index='Year',   # Column to turn into new index
    columns='Sex',  # Column to turn into new columns
    values='Count', # Column to aggregate for values
    aggfunc=sum)    # Aggregation function
mf_pivot


# Notice that the data values are identical in the pivot table and the table
# produced with `.groupby()`; the values are just arranged differently. Pivot
# tables are useful for quickly summarizing data using two attributes and are
# often seen in articles and papers.
# 
# The `pd.DataFrame.plot()` function also happens to work well with pivot tables,
# since the function draws one line for each column of data in the table:

# In[17]:


mf_pivot.plot();


#!/usr/bin/env python
# coding: utf-8

# In[27]:


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


# # Subsetting
# 

# This section introduces operations for taking subsets of dataframes. When data
# scientists first read in a dataframe, they often want to subset the specific
# data that they plan to use. For example, a data scientist can *slice* out the
# ten relevant features from a dataframe with hundreds of columns. Or, they can
# *filter* a dataframe to remove rows with incomplete data. For the rest of this
# chapter, we'll introduce dataframe operations using a dataframe of baby names.

# ## About the Data

# There's a 2021 New York Times article that talks about Prince Harry and
# Meghan's unique choice for their new baby daughter's name: Lilibet
# {cite}`williamsLilith2021`. The article has an interview with Pamela Redmond,
# an expert on baby names, who talks about interesting trends in how people name
# their kids. For example, she says that names that start with the letter "L"
# have become very popular in recent years, while names that start with the
# letter "J" were most popular in the 1970s and 1980s. Are these claims reflected
# in data? We can use `pandas` to find out.

# First, import the package as `pd`, the canonical abbreviation:

# In[28]:


import pandas as pd


# We have a dataset of baby names stored in a comma-separated values (CSV) file
# called `babynames.csv`. Use the `pd.read_csv` function to read the file as a
# `pandas.DataFrame` object.

# In[29]:


baby = pd.read_csv('babynames.csv')
baby


# The data in the `baby` table comes from the US Social Security department,
# which records the baby name and birth sex for birth certificate purposes. They
# make the baby names data available on their website {cite}`babynamesData`.
# We've loaded this data into the `baby` table.

# The Social Security website has a page that describes the data in more detail
# ([link](https://www.ssa.gov/oact/babynames/background.html)). We won't go
# in-depth in this chapter about the data's limitations, but we'll point out
# this relevant quote from the website:
# 
# > All names are from Social Security card applications for births that occurred
# > in the United States after 1879. Note that many people born before 1937 never
# > applied for a Social Security card, so their names are not included in our
# > data. For others who did apply, our records may not show the place of birth,
# > and again their names are not included in our data.
# >
# > All data are from a 100% sample of our records on Social Security card
# > applications as of March 2021.

# ## DataFrames and Indices

# Let's examine the `baby` dataframe in more detail. A dataframe has rows and
# columns. Every row and column has a label, as highlighted in
# {numref}`fig:baby-labels`. 
# 
# ```{figure} figures/baby-labels.svg
# ---
# name: fig:baby-labels
# alt: baby-labels
# ---
# The `baby` dataframe has labels for both rows and columns (boxed).
# ```

# By default, `pandas` assigns row labels as incrementing numbers starting from
# 0. In this case, the data at the row labeled `0` and column labeled `Name` has
# the data `'Liam'`.
# 
# Dataframes can also have strings as row labels. {numref}`fig:dog-labels` shows
# a dataframe of dog data where the row labels are strings.
# 
# ```{figure} figures/dog-labels.svg
# ---
# name: fig:dog-labels
# alt: dog-labels
# ---
# Row labels in dataframes can also be strings. In this example, each row is
# labeled using the dog breed name.
# ```

# The row labels have a special name. We call them the **index** of a dataframe,
# and `pandas` stores the row labels in a special `pandas.Index` object. We won't
# discuss the `pandas.Index` object since it's not very common to manipulate the
# index itself. But, it's important to remember that even though the index looks
# like a column of data, the index really represents row labels, not data. For
# instance, the dataframe of dog breeds has 4 columns of data, not 5, since
# the index doesn't count as a column.

# ## Slicing
# 
# *Slicing* is an operation that creates a new dataframe by taking a subset of
# rows or columns out of another dataframe. Think about slicing a tomato---slices
# can go both vertially and horizontally. To take slices of a dataframe in
# `pandas`, we use the `.loc` and `.iloc` properties. Let's start with `.loc`.
# 
# Here's the full `baby` dataframe:

# In[30]:


baby


# `.loc` lets you select rows and columns using their labels. For example, to get the data in the row labeled `1` and column labeled `Name`:

# In[31]:


#        The first argument is the row label
#        ↓
baby.loc[1, 'Name']
#            ↑
#            The second argument is the column label


# :::{warning}
# Notice that `.loc` needs brackets; running `baby.loc(1, 'Name')` will error.
# :::

# To slice out multiple rows or column, you can use Python slice syntax instead
# of individual values:

# In[32]:


baby.loc[0:3, 'Name':'Count']


# To get an entire column of data, pass an empty slice as the first argument:

# In[33]:


baby.loc[:, 'Count']


# Notice that the output of this doesn't look like a dataframe, and it's not.
# Selecting out a single row or column of a dataframe produces a `pd.Series`
# object.

# In[34]:


counts = baby.loc[:, 'Count']
counts.__class__.__name__


# What's the difference between a `pd.Series` and `pd.DataFrame` object?
# Essentially, a `pd.DataFrame` is two-dimensional---it has rows and columns and
# represents a table of data. A `pd.Series` is one-dimensional---it represents a
# list of data. `pd.Series` and `pd.DataFrame` objects have many methods in
# common, but they really represent two different things. Confusing the two can
# cause bugs and confusion.
# 
# To select specific columns of a dataframe, pass a list into `.loc`:

# In[35]:


# Here's the original dataframe
baby


# In[36]:


# And here's the dataframe with only Name and Year columns
baby.loc[:, ['Name', 'Year']]
#           └-------┬------┘
#                   |
#         list of column labels


# Selecting columns is very common, so there's a shorthand.

# In[37]:


# Shorthand for baby.loc[:, 'Name']
baby['Name']


# In[38]:


# Shorthand for baby.loc[:, ['Name', 'Count']]
baby[['Name', 'Count']]


# Slicing using `.iloc` works similarly to `.loc`, except that `.iloc` uses the
# *positions* of rows and columns rather than labels. It's easiest to show the
# difference between `.iloc` and `.loc` when the dataframe index has strings, so
# for demonstration purposes let's look at a dataframe with information on dog
# breeds:

# In[39]:


dogs = pd.read_csv('dogs.csv', index_col='breed')
dogs


# To get the first three rows and first two columns by position, use `.iloc`:

# In[40]:


dogs.iloc[0:3, 0:2]


# The same operation using `.loc` requires you to use the dataframe labels:

# In[41]:


dogs.loc['Labrador Retriever':'Beagle', 'grooming':'food_cost']


# ## Filtering Rows

# So far, we've shown how to use `.loc` and `.iloc` to slice a dataframe using
# labels and positions.
# 
# However, data scientists often want to *filter* rows---they want to take
# subsets of rows using some criteria. Let's say you want to find the most
# popular baby names in 2020. To do this, you can filter rows to keep only the
# rows where the `Year` is 2020.
# 
# To filter, you can 1) check whether each value in the `Year`
# column is equal to 1970, then 2) keep only those rows.
# 
# To compare each value in `Year`, slice out the column and make a boolean
# comparison. (This is similar to what you would do with a `numpy` array.)

# In[42]:


# Here's the dataframe for reference
baby


# In[43]:


# Get a Series with the Year data
baby['Year']


# In[44]:


# Compare with 2020
baby['Year'] == 2020


# Notice that a boolean comparison on a Series gives a Series of booleans. This
# is nearly equivalent to writing:
# 
# ```python
# is_2020 = []
# for value in baby['Year']:
#     is_2020.append(value == 2020)
# ```
# 
# But the boolean comparison is easier to write and much faster to execute than a
# `for` loop.

# Now, we tell `pandas` to keep only the rows where the comparison evaluated to `True`:

# In[45]:


# Passing a Series of booleans into .loc only keeps rows where the Series has
# a True value.
#        ↓
baby.loc[baby['Year'] == 2020, :]


# In[46]:


# Filtering has a shorthand. This computes the same table as the snippet above
# without using .loc
baby[baby['Year'] == 2020]


# Finally, to find the most common names in 2020, sort the dataframe by `Count`
# in descending order.

# In[47]:


# When you have a long expression, you can wrap it in parentheses, then add
# line breaks to make it more readable.
(baby[baby['Year'] == 2020]
 .sort_values('Count', ascending=False)
 .head(7) # take the first seven rows
)


# ## Example: How recently has Luna become a popular name?
# 
# The New York Times article mentions that the name "Luna" was almost nonexistent
# before 2000 but has since grown to become a very popular name for girls. We can
# check this using slicing and filtering. When approaching a data manipulation
# task, we recommend you start by breaking the problem down into steps. For
# example, you could think:
# 
# 1. Filter: keep only rows with `'Luna'` in the `Name` column.
# 1. Filter: keep only rows with `'F'` in the `Sex` column.
# 1. Slice: keep the `Count` and `Year` columns.
# 
# Now, it's a matter of translating each step into code.

# In[48]:


luna = baby[baby['Name'] == 'Luna'] # [1]
luna = luna[luna['Sex'] == 'F']     # [2]
luna = luna[['Count', 'Year']]      # [3]
luna


# `pandas` has some plotting functionality. We won't go in-depth in plotting here
# since we talk more about plotting in the Visualization chapter. But for now,
# remember that you can use `.plot()` on a dataframe to make a few simple plots.

# In[49]:


#         x-axis  y-axis
luna.plot('Year', 'Count');


# It's just as the article says. Luna wasn't popular at all until the year 2000
# or so. Think about that---if someone tells you that their name is Luna, you can
# take a pretty good guess at their age even without any other information about
# them!
# 
# Just for fun, here's the same plot for the name Siri.

# In[50]:


# Using .query is similar to using .loc with a boolean series. query() has more
# restrictions on what kinds of filtering you can do but can be convenient as a
# shorthand. 
(baby.query('Name == "Siri"')
 .query('Sex == "F"')
 .plot('Year', 'Count')
);


# Why might the popularity have dropped so suddenly? Well, Siri happens to be the
# name of the voice assistant for Apple products and was introduced in 2011.
# Let's draw a line for the year 2011 and take a look...

# In[51]:


(baby.query('Name == "Siri"')
 .query('Sex == "F"')
 .plot('Year', 'Count')
)
plt.axvline(2011, c='red');


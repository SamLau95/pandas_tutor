# these will all get parsed into PassThroughCalls since we can only robustly
# create GroupbyFilerCalls during runtime analysis, so this test isn't really
# testing that much, but oh well!

(dogs
 .groupby('size')
 .filter(lambda df: df.shape[0] > 2)
)

(dogs
 .groupby('size')
 .filter(lambda df: df.shape[0] > 2, dropna=False)
)

# no groupby, so it shouldn't get parsed into a GroupByFilterCall
df.filter(items=['one', 'three'])

# can't handle this at parse time, so we'll just pass it through
(dogs
 .groupby('size')
 ['weight']
 .filter(lambda x: x.shape[0] > 2, dropna=False)
)
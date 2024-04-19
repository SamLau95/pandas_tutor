(dogs
 .groupby('grooming')
 .agg('mean')
)

(dogs
 .groupby('grooming')
 .var()
)

# Note that this is an agg but we have to handle it at runtime, not parse time
(dogs
 .groupby('grooming')
 ['weight']
 .var()
)

# should not be parsed into an AggCall
(dogs
 .groupby('grooming')
 .transform(lambda x: x.max() - x.min())
)

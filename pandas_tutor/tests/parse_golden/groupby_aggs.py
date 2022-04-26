(dogs
 .groupby('grooming')
 .agg('mean')
)

(dogs
 .groupby('grooming')
 .var()
)

# should not be parsed into an AggCall
(dogs
 .groupby('grooming')
 .transform(lambda x: x.max() - x.min())
)

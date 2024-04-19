### `mark_for_get`
```python
df.get(['Name'])
```

### `mark_for_sort_values`
```python
df.sort_values('Name')
```

### `mark_for_drop`
```python
dogs.drop(columns=['type', 'price'])
```

### `mark_for_rename`
```python
df.rename(index={'sam': 'smae'})
```

### `mark_for_head_or_tail`
```python
df.head(2)
df.tail()
```

### `mark_for_apply`
```python
df['breed'].apply(len)
```

### `mark_for_assign`
```python
dogs.assign(daily=lambda df: df['food_cost'] * 30)
```

### `mark_for_groupby`
```python
df.groupby('hello')
```

### `mark_for_agg`
NO TEST FOR AGG

### `mark_for_reset_index`
```python
dogs.reset_index(level=[1, 2], drop=True)
```
Sam doesn't think this works properly

### `mark_for_set_index`
```python
dogs.set_index('price')
```

### `mark_for_unstack`
```python
counts.unstack(level=-1, fill_value=0)
```

### `mark_for_stack`
```python
counts.stack(level=-1, drop_na=False)
```

### `mark_for_pivot`
```python
df.pivot(index='foo', columns='bar', values='baz')
```

### `mark_for_pivot_table`
```python
df.pivot(index='foo', columns='bar', values='baz')
```
mark_for_pivot vs. mark_for_pivot_table ???

### `mark_for_melt`
NO TEST FOR mark_for_melt

### `mark_for_bool_expr`
```python
(df['Count'] > 13000) & (df['Count'] < 15000)
(df.get('Count') > 13000) & (df.get('Sex') == 'M')
```

### `mark_for_subscript`
```python
df.loc[1:5, ['Name', 'Count']]
df.iloc[2:5, 1:4] 
df[df['Count'] > 10000]
df.groupby('Sex')[['Count']]
```

Uses `mark_for_subscript_df_to_df`, `make_subscript_comparison_marks`, `mark_for_subscript_of_series`, `mark_for_subscript_into_series`, `mark_for_subscript_into_scalar`

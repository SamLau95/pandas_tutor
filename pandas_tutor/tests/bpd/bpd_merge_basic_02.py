import babypandas as bpd

phones = bpd.DataFrame().assign(
    Model=['iPhone 13', 'iPhone 13 Pro Max', 'Samsung Galaxy Z Flip', 'Pixel 5a'],
    Price=[799, 1099, 999, 449],
    Screen=[6.1, 6.7, 6.7, 6.3]
)

inventory = bpd.DataFrame().assign(
    Handset=['iPhone 13 Pro Max', 'iPhone 13', 'Pixel 5a', 'iPhone 13'],
    Units=[50, 40, 10, 100],
    Store=['Westfield UTC', 'Westfield UTC', 'Fashion Valley', 'Downtown']
)

phones.merge(inventory, left_on='Model', right_on='Handset')


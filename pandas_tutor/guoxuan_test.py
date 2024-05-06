# head
import pandas as pd
import numpy as np
import io

num_rows = 20
num_columns = 20

testing = pd.DataFrame(
    np.random.rand(num_rows, num_columns),
    columns=[f"col{i}" for i in range(num_columns)],
)

testing.head()
# testing.head(-10)
# testing.head(0)
# testing.head(15)
testing["col0"].head()


# sort_values
import pandas as pd
import numpy as np
import io

num_rows = 20
num_columns = 20

testing = pd.DataFrame(
    np.random.rand(num_rows, num_columns),
    columns=[f"col{i}" for i in range(num_columns)],
)

testing.sort_values("col0")
# testing.sort_values(['col0', 'col19'])
testing["col0"].sort_values()

# loc/iloc

import pandas as pd
import numpy as np
import io

num_rows = 20
num_columns = 20

testing = pd.DataFrame(
    np.random.rand(num_rows, num_columns),
    columns=[f"col{i}" for i in range(num_columns)],
)

testing.loc[[0, 1, 6], ["col0", "col5", "col18"]]
testing.iloc[[0, 4, 18], [0, 5, 10]]
testing["col0"].iloc[[0, 1, 2]]

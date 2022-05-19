"""
defines %%python_tutor magic
"""

from typing import Any, Dict
from IPython.core.magic import (
    Magics,
    cell_magic,
    magics_class,
    needs_local_scope,
)
from IPython.display import HTML, Javascript, display

from pandas_tutor.__main__ import make_tutor_spec_ipython

# runs on initial load to load the wst js library
_initialize_js = """
console.log("initializing pandas_tutor js")
"""

# displays each time a cell with %%pandas_tutor is run
_viz_html = """
<pre class="pandas_tutor_output">
{spec}
</pre>
"""


@magics_class
class PandasTutorMagics(Magics):

    # inherits self.shell from Magics

    def __init__(self, shell, **kwargs):
        super().__init__(shell, **kwargs)
        display(Javascript(_initialize_js))

    @cell_magic
    def pandas_tutor(self, line: str, cell: str):
        spec = make_tutor_spec_ipython(cell, self.shell)
        display(HTML(_viz_html.format(spec=spec)))

    # %%pt is an alias for %%pandas_tutor
    @cell_magic
    def pt(self, line: str, cell: str):
        return self.pandas_tutor(line, cell)

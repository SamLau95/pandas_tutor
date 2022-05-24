"""
defines %%python_tutor magic
"""
import json

from IPython.core.magic import (
    Magics,
    cell_magic,
    magics_class,
)
from IPython.display import HTML, display

from pandas_tutor.__main__ import make_tutor_spec_ipython

# runs on initial load to load the wst js library
#
# loads the global variable createWsvFromPandasTrace
_load_wst_bundle = """
<script type="text/javascript" src="https://cokapi.com/wst-pg-devel/wst/wsapp/frontend/build/wsembed.bundle.js"></script>
<script>
console.log("initializing pandas_tutor js")
</script>
"""  # noqa: E501

# displays each time a cell with %%pandas_tutor is run
_viz_html = """
<div class="pt-viz" id="{viz_id}"></div>
<script>
createWsvFromPandasTrace('#{viz_id}', {spec});
</script>
"""


@magics_class
class PandasTutorMagics(Magics):

    viz_count = 0

    def __init__(self, shell, **kwargs):
        super().__init__(shell, **kwargs)
        display(HTML(_load_wst_bundle))

    @cell_magic
    def pandas_tutor(self, line: str, cell: str):
        # inherits self.shell from Magics parent class
        spec = make_tutor_spec_ipython(cell, self.shell)
        # need to double wrap so that quotes and \n are escaped
        spec_json = json.dumps(spec)

        viz_id = f"pt-viz-{self.viz_count}"
        make_viz = _viz_html.format(viz_id=viz_id, spec=spec_json)
        display(HTML(make_viz))

        # increment so that each cell gets a unique css id
        self.viz_count += 1

    # %%pt is an alias for %%pandas_tutor
    @cell_magic
    def pt(self, line: str, cell: str):
        return self.pandas_tutor(line, cell)

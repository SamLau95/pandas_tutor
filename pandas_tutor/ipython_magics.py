"""
defines %%pandas_tutor magic
"""
import ast
import json

from IPython.core.magic import (
    Magics,
    line_cell_magic,
    cell_magic,
    magics_class,
)
from IPython.display import HTML, display

import pandas_tutor.__main__ as pt
import pandas_tutor.util as util

if util.in_dev():
    wsembed_bundle_url = "https://cokapi.com/wst-pg-devel/wst/wsapp/frontend/build/wsembed.bundle.js"  # noqa: E501
else:
    wsembed_bundle_url = "https://pandastutor.com/build/wsembed.bundle.2022-07-07-release.js"  # noqa: E501

# when using projectors we need stronger colors, otherwise people can't
# distinguish between colors
#
# colors from https://colorbrewer2.org/#type=qualitative&scheme=Set1&n=9
projector_colors = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#a65628",
    "#f781bf",
    "#999999",
]

default_wsv_colors = [
    "#a6cee3",
    "#b2df8a",
    "#fb9a99",
    "#fdbf6f",
    "#cab2d6",
    "#ff7f00",
    "#33a02c",
    "#6a3d9a",
    "#e31a1c",
    "#1f78b4",
    "#b15928",
    "#ffff99",
]


# runs on initial load to load the wst js library
#
# HACK: use setTimeout to avoid race condition with loading pandas tutor JS
_load_wst_bundle = f"""
<script type="text/javascript" src="{wsembed_bundle_url}"></script>
<script>
console.log("initializing pandas_tutor js")

function drawWsv(viz_id, spec, options) {{
  if (typeof createWsvFromPandasTrace === 'undefined') {{
    setTimeout(() => drawWsv(viz_id, spec, options), 2000) // retry in 2 seconds
    return
  }}
  createWsvFromPandasTrace(viz_id, spec, options)
}}
</script>
"""  # noqa: E501

# displays each time a cell with %%pandas_tutor is run
_viz_html = """
<div class="pt-viz" id="{viz_id}"></div>
<script>
drawWsv('#{viz_id}', {spec}, {options});
</script>
"""


@magics_class
class PandasTutorMagics(Magics):

    viz_count = 0

    display_options: dict = {
        "nohover": True,
        "maxDisplayRows": 7,
        "maxDisplayCols": 5,
    }

    def __init__(self, shell, **kwargs):
        super().__init__(shell, **kwargs)
        display(HTML(_load_wst_bundle))

    @line_cell_magic
    def set_pandas_tutor_options(self, line: str, cell=None):
        """
        used to set display options using a python dict. example:

        %%set_pandas_tutor_options
        { "maxDisplayRows": 10, "maxDisplayCols": 5 }

        options:

        - maxDisplayRows: maximum number of rows to display in the table
        - maxDisplayCols: maximum number of columns to display in the table
        - nohover: if True, the table will not show hover effects
        - projectorMode: if True, use bolder colors for projectors
        """
        opts = ast.literal_eval(cell if cell else line)
        if not isinstance(opts, dict):
            raise ValueError("options must be a dict")

        if "projectorMode" in opts:
            if opts.pop("projectorMode"):
                self.display_options["colorPalette"] = projector_colors
            else:
                # TODO: can we just delete the key? neither way seems to
                # update the wsv colors after setting projectorMode
                self.display_options["colorPalette"] = default_wsv_colors
        self.display_options.update(opts)

    @cell_magic
    def pandas_tutor(self, line: str, cell: str):
        # inherits self.shell from Magics parent class
        spec = pt.make_tutor_spec_ipython(cell, self.shell)
        # need to double wrap so that quotes and \n are escaped
        spec_json = json.dumps(spec)

        viz_id = f"pt-viz-{self.viz_count}"
        options = json.dumps(self.display_options)
        make_viz = _viz_html.format(
            viz_id=viz_id, spec=spec_json, options=options
        )
        display(HTML(make_viz))

        # increment so that each cell gets a unique css id
        self.viz_count += 1

    # %%pt is an alias for %%pandas_tutor
    @cell_magic
    def pt(self, line: str, cell: str):
        return self.pandas_tutor(line, cell)

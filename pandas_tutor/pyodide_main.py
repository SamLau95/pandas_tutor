# type: ignore
# main entry point for running in pyodide

# 2022-05-09: this file is deprecated since i learned how to call main.make_tutor_spec(userCode) directly from pyodide JS

from .main import make_tutor_spec

import js


def create_trace_from_js():
    return make_tutor_spec(js.globalUserCode)

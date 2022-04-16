# main entry point for running in pyodide

from .main import make_tutor_spec

import js
def create_trace_from_js(): # type: ignore
    return make_tutor_spec(js.globalUserCode)

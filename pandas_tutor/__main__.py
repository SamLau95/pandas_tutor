"""
runs pandas_tutor backend

Usage:
    pandas_tutor FILE ... [--output] [--parse_only] [--parse_log]
    pandas_tutor -c CODE

Options:
    -o --output      # Outputs specs to files named {input_file}.golden
    -p --parse_only  # Outputs parsed code rather than full spec
    -l --parse_log   # Outputs parse debug output
    -c --code        # Code as a string (instead of a file)
"""

from pathlib import Path

from docopt import docopt

from .diagram import OutputSpec
from .parse import parse, parse_as_json, test_logger
from .run import run
from .serialize import serialize


def make_tutor_spec(code: str) -> str:
    """oh yeah, it's all coming together"""
    root = parse(code)
    eval_results = run(root)
    explanation = serialize(eval_results)
    spec = OutputSpec(code=code, explanation=explanation)
    return spec.to_json()


def make_tutor_spec_ipython(code: str, ipython_shell) -> str:
    """
    when we run in ipython, we need to execute code using ipython's namespace
    """
    root = parse(code)
    eval_results = run(root, ipython_shell)
    explanation = serialize(eval_results)
    spec = OutputSpec(code=code, explanation=explanation)
    return spec.to_json()


def make_tutor_spec_py(code: str) -> OutputSpec:
    """Keeps serialized output as a Python object for testing"""
    root = parse(code)
    eval_results = run(root)
    explanation = serialize(eval_results)
    spec = OutputSpec(code=code, explanation=explanation)
    return spec


def spec_from_file(filename: str, spec_fn=make_tutor_spec) -> str:
    code = Path(filename).read_text()
    return spec_fn(code)


def write_spec_to_file(spec: str, out: Path) -> None:
    print(f"Writing {out}")
    with out.open("w") as f:
        f.write(spec)


if __name__ == "__main__":
    doc = __doc__ or ""
    args = docopt(doc, version="1.0")

    spec_fn = (
        test_logger
        if args["--parse_log"]
        else parse_as_json
        if args["--parse_only"]
        else make_tutor_spec
    )

    if args["--code"]:
        code = args["CODE"]
        print(spec_fn(code))
    if not args["--output"]:
        for filename in args["FILE"]:
            print(spec_from_file(filename, spec_fn)) # type: ignore
    else:
        for filename in args["FILE"]:
            spec = spec_from_file(filename, spec_fn) # type: ignore
            out_filename = Path(filename + ".golden")
            write_spec_to_file(spec, out_filename)

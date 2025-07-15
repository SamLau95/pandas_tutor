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

import argparse
from pathlib import Path

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


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="runs pandas_tutor backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add positional arguments for files
    parser.add_argument(
        "files", nargs="*", metavar="FILE", help="Input files to process"
    )

    # Add optional arguments
    parser.add_argument(
        "-c",
        "--code",
        metavar="CODE",
        help="Code as a string (instead of a file)",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Outputs specs to files named {input_file}.golden",
    )
    parser.add_argument(
        "-p",
        "--parse_only",
        action="store_true",
        help="Outputs parsed code rather than full spec",
    )
    parser.add_argument(
        "-l",
        "--parse_log",
        action="store_true",
        help="Outputs parse debug output",
    )

    parser.add_argument("--version", action="version", version="1.0")

    return parser


def main():
    """Main entry point for the pandas_tutor command"""
    parser = create_parser()
    args = parser.parse_args()

    # Validate that either files or code is provided
    if not args.code and not args.files:
        parser.error("Must provide either files or --code argument")

    spec_fn = (
        test_logger
        if args.parse_log
        else parse_as_json
        if args.parse_only
        else make_tutor_spec
    )

    if args.code:
        print(spec_fn(args.code))

    if args.files:
        if not args.output:
            for filename in args.files:
                print(spec_from_file(filename, spec_fn))  # type: ignore
        else:
            for filename in args.files:
                spec = spec_from_file(filename, spec_fn)  # type: ignore
                out_filename = Path(filename + ".golden")
                write_spec_to_file(spec, out_filename)


if __name__ == "__main__":
    main()

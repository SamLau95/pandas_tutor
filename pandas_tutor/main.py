'''
functions that put everything together

Usage:
    main.py FILE ... [-o] [--parse_only]

Options:
    -o --output   # Outputs specs to files named {input_file}.golden
    --parse_only  # Outputs parsed code rather than full spec
'''
import dataclasses
import typing as t
from pathlib import Path

from docopt import docopt  # type: ignore

from .parse import parse, parse_as_json
from .run import run
from .serialize import serialize, serialize_to_json


def make_tutor_spec(code: str) -> str:
    root = parse(code)
    eval_results = run(root)
    spec = serialize_to_json(eval_results)
    return spec


def make_tutor_spec_py(code: str) -> t.List[dict]:
    '''Keeps serialized output as a Python object for testing'''
    root = parse(code)
    eval_results = run(root)
    spec = serialize(eval_results)
    return [dataclasses.asdict(diagram) for diagram in spec]


def spec_from_file(filename: str, spec_fn=make_tutor_spec) -> str:
    code = Path(filename).read_text()
    return spec_fn(code)


def write_spec_to_file(spec: str, out: Path) -> None:
    print(f'Writing {out}')
    with out.open('w') as f:
        f.write(spec)
        f.write('\n')


if __name__ == "__main__":
    args = docopt(__doc__, version='1.0')
    # print(args)
    spec_fn = make_tutor_spec if not args['--parse_only'] else parse_as_json

    if not args['--output']:
        for filename in args['FILE']:
            print(spec_from_file(filename, spec_fn))
    else:
        for filename in args['FILE']:
            spec = spec_from_file(filename, spec_fn)
            out_filename = Path(filename + '.golden')
            write_spec_to_file(spec, out_filename)

'''
functions that put everything together
'''
import typing as t
import dataclasses

from .parse import parse
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

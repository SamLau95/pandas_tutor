import sys
print("print to stdout")
sys.stderr.write("print to stderr")
print("print again to stderr", file=sys.stderr)

# tests that pointers still trigger memory cap


class MyStr:
    def __init__(self, val):
        self.val = val


# this uses about 2.5 MB
# but, sys.getsizeof() only returns ~120 KB
hello = [MyStr('hello world') for _ in range(15_000)]

hello[:5]

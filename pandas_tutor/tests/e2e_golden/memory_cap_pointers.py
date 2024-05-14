# tests that pointers still trigger memory cap


class MyStr:
    def __init__(self, val):
        self.val = val


# this uses about 115 MB
# but, sys.getsizeof() only returns ~120 KB (updated 5/13/2024, don't know how big sys.getsizeof() thinks it is)
hello = [MyStr("hello world") for _ in range(750_000)]

hello[:5]

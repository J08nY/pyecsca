cdef class Test:
    def __init__(self):
        print("here")

cdef class SubTest(Test):
    def __init__(self):
        print("sub init")

cdef class OtherTest(Test):
    def __init__(self):
        print("other init")

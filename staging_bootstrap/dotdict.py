"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

class DotDict(dict):
    """Extends a dictionary to be accessed in dotted notation"""

    def __init__(self, values):
        super(DotDict, self).__init__(self)
        for key, value in values.items():
            self.__setattr__(key, value)

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = DotDict(value)
        dict.__setitem__(self, key, value)

    def __getattr__(self, key):
        return dict.__getitem__(self, key)

# vi: ts=4 et:

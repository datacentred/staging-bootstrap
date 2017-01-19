"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

class PuppetConfig(object):
    """Wraps up a puppet configuration file"""

    def __init__(self, value):
        self.value = value

    @property
    def config(self):
        """Renders a configuration file"""
        text = ''
        for section in self.value:
            text += "[{}]\n".format(section)
            for option in self.value[section]:
                text += "{} = {}\n".format(option, self.value[section][option])
        return text


# vi: ts=4 et:

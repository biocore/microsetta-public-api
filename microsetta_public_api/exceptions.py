# Value errors
class UnknownID(ValueError):
    pass


class UnknownMetric(ValueError):
    pass


# Key errors
class DisjointError(KeyError):
    pass


# Type errors
class ConfigurationError(TypeError):
    pass

__all__ = ['server', 'api', 'config', 'exceptions',
           ]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from typing import Dict

from microsetta_public_api.backend import constructors
from microsetta_public_api.config import (
    SERVER_CONFIG,
)


class Component:

    def __init__(self, name):
        self.name = name
        self.data = None
        self.children: Dict[str, 'Component'] = dict()

    def add_child(self, child: 'Component'):
        self.children.update({child.name: child})
        return child

    def set(self, other: 'Component'):
        self.name = other.name
        self.data = other.data
        self.children = other.children

    def set_data(self, data: object):
        self.data = data

    def get_data(self):
        return self.data

    def get_child(self, name: str) -> 'Component':
        try:
            return self.children[name]
        except KeyError:
            raise KeyError(name)

    def gets(self, *args):
        if len(args) == 0:
            return self
        first = args[0]
        rest = args[1:]
        child = self.get_child(first)
        return child.gets(*rest)

    def has(self, *args):
        if len(args) == 0:
            return True
        first = args[0]
        rest = args[1:]
        if first in self.children:
            return self.get_child(first).has(*rest)
        else:
            return False

    def remove_child(self, name: str):
        del self.children[name]

    @staticmethod
    def from_dict(dict_, default_name='root', dry_run=False):
        root = Component(default_name)
        Component._from_dict_helper(dict_, root, dry_run)
        return root

    @staticmethod
    def _from_dict_helper(dict_, parent, dry_run):
        for name, value in dict_.items():
            new_ = Component(name)
            if 'construct' in value and not dry_run:
                constructor = constructors[value['construct']]
                config = value.get('config', dict())
                new_.data = constructor().load(**config)

            children = value.get('components', dict())
            Component._from_dict_helper(children, new_, dry_run)
            parent.add_child(new_)

    def __str__(self):
        return self._str()

    def _str(self, level: int = 0):
        name = self.name
        left_spacing = level * '\t'
        return left_spacing + 'Name: ' + name + '\n' +\
            left_spacing + 'Data: ' + str(self.data) + '\n' +\
            left_spacing + ('Children:' if self.children else '') + '\n' +\
            ''.join(child._str(level + 1) for child in self.children.values())


resources_alt = Component.from_dict(SERVER_CONFIG['resources'])

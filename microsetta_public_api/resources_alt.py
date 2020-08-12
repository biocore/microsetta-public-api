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
        self.parent = None

    def add(self, child: 'Component'):
        self.children.update({child.name: child})

    def set(self, other: 'Component'):
        self.__dict__ = other.__dict__

    def set_data(self, component: object):
        self.data = component

    def get(self, name: str) -> 'Component':
        try:
            return self.children[name]
        except KeyError:
            raise KeyError(name)

    def gets(self, *args):
        # TODO test this
        if len(args) == 0:
            return self
        first = args[0]
        rest = args[1:]
        child = self.get(first)
        if rest:
            return child.gets(*rest)
        return child

    def has(self, *args):
        if len(args) > 1:
            # TODO
            pass
        raise NotImplementedError()

    def remove(self, name: str):
        del self.children[name]

    def set_parent(self, parent: 'Component'):
        self.parent = parent

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
            parent.add(new_)
            new_.set_parent(parent)

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

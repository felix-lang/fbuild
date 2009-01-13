"""The config system is a simple mechanism in order to model testing similar
tests."""

import fbuild.db

# ------------------------------------------------------------------------------

class Options:
    def __init__(self):
        self.field_names = []
        self.fields = []

    def add_field(self, key, value):
        self.field_names.append(key)
        self.fields.append(value)

    def update(self, options):
        self.field_names.extend(options.field_names)
        self.fields.extend(options.fields)

class _FieldTable(dict):
    """A dictionary that stores Just a dict that records the order of the
    stored items."""

    def __init__(self):
        self.field_names = []

    def __setitem__(self, key, value):
        if key not in self:
            self.field_names.append(key)

        super().__setitem__(key, value)

class TestMeta(fbuild.db.PersistentMeta):
    @classmethod
    def __prepare__(cls, name, bases):
        return _FieldTable()

    def __new__(cls, name, bases, attrs):
        parents = [base for base in bases if isinstance(base, TestMeta)]

        if not parents:
            return super().__new__(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super().__new__(cls, name, bases, {'__module__': module})
        new_class.add_to_class('__meta__', Options())

        for parent in parents:
            if hasattr(parent, '__meta__'):
                new_class.__meta__.update(parent.__meta__)

        # add the fields in the order that they were declared
        for key in attrs.field_names:
            try:
                value = attrs[key]
            except KeyError:
                pass
            else:
                new_class.add_to_class(key, attrs[key])

        return new_class

    def add_to_class(cls, key, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, key)
        else:
            setattr(cls, key, value)

class Test(metaclass=TestMeta):
    pass

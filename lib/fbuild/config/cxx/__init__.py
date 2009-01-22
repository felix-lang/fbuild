import fbuild.config.c as c
import fbuild.config.c.c90 as c90

function_test = c.function_test
macro_test = c.macro_test
type_test = c.type_test
int_type_test = c.int_type_test

class struct_test(c.struct_test):
    def contribute_to_class(self, cls, key):
        # c++ doesn't need "struct" prepended to the typename.
        self.__name__ = key
        if self.name is None:
            self.name = key
        cacheproperty(self).contribute_to_class(cls, key)

variable_test = c.variable_test

# ------------------------------------------------------------------------------

Test = c.Test

class HeaderMeta(c.HeaderMeta):
    def __new__(cls, name, bases, attrs):
        namespace = attrs.pop('namespace', None)

        new_class = super().__new__(cls, name, bases, attrs)

        if namespace is not None:
            for name, field in new_class.fields():
                # Macros shouldn't get the namespace prepended.
                if not isinstance(field.method, macro_test):
                    field.method.name = namespace + '::' + field.method.name

        return new_class

class Header(c.Header, metaclass=HeaderMeta):
    namespace = None

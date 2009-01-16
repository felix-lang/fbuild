import textwrap

import fbuild.config
import fbuild.db

# ------------------------------------------------------------------------------

class Function:
    """L{Function} describes the features of a function.  It contains the
    return type of the function as well as the types of the arguments."""

    def __init__(self, return_type, *args):
        self.return_type = return_type
        self.args = args

    def __repr__(self):
        return '%s(%r%s)' % (
            self.__class__.__name__,
            self.return_type,
            ', ' + ', '.join(repr(a) for a in self.args) if self.args else '',
        )

    def __eq__(self, other):
        return \
            type(self) is type(other) and \
            self.return_type == other.return_type and \
            self.args == other.size

    def __hash__(self):
        return hash((self.__class__, self.return_type, self.args))

class Macro:
    """L{Macro} describes the features of a macro.  It contains no data."""

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(self.__class__)

class Type:
    """L{Type} describes the features of a type.  It contains the type's
    alignment and size."""

    def __init__(self, alignment, size):
        self.alignment = alignment
        self.size = size

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.alignment,
            self.size,
        )

    def __eq__(self, other):
        return \
            type(self) is type(other) and \
            self.alignment == other.alignment and \
            self.size == other.size

    def __hash__(self):
        return hash((self.__class__, self.alignment, self.size))

class IntType(Type):
    """L{IntType} describes L{Type}s that are mapped to an integer type.  It
    contains the type's alignment, size, and sign."""

    def __init__(self, alignment, size, signed):
        super().__init__(alignment, size)
        self.signed = signed

    def __repr__(self):
        return '%s(%r, %r, %r)' % (
            self.__class__.__name__,
            self.alignment,
            self.size,
            self.signed,
        )

    def __eq__(self, other):
        return \
            type(self) is type(other) and \
            self.alignment == other.alignment and \
            self.size == other.size and \
            self.signed == other.signed

    def __hash__(self):
        return hash((self.__class__, self.alignment, self.size, self.signed))

class Struct:
    """L{Struct} describes a struct type.  It contains the type and name of all
    of the structures's members."""

    def __init__(self, *members):
        self.members = members

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', ' + ', '.join(repr(m) for m in self.members) if members else '',
        )

    def __eq__(self, other):
        return \
            type(self) is type(other) and \
            self.members == other.members

    def __hash__(self):
        return hash((self.__class__, self.members))

class Variable:
    """L{Variable} describes a global variable.  It contains no data."""

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(self.__class__)

# ------------------------------------------------------------------------------

class cacheproperty(fbuild.db.cacheproperty):
    def contribute_to_class(self, cls, key):
        """Register itself inside the class."""

        self.__name__ = key
        cls.__meta__.add_field(key, self)
        setattr(cls, key, self)

# ------------------------------------------------------------------------------

class AbstractFieldDescriptor:
    """L{AbstractFieldDescriptor} represents a descriptor for the L{Test} class
    that when accessed, evaluates a cache and returns the appropriate field if
    the cache passes. Otherwise, it returns I{None}."""

    def __init__(self, *,
            attribute=None,
            name=None,
            test=None,
            stdin=None,
            stdout=None,
            timeout=None):
        self.__name__ = attribute
        self.name = name
        self.test = test
        self.stdin = stdin
        self.stdout = stdout
        self.timeout = timeout

    def contribute_to_class(self, cls, key):
        self.__name__ = key
        if self.name is None:
            self.name = key
        cacheproperty(self).contribute_to_class(cls, key)

    def __call__(self, instance):
        # We couldn't find a previous call to this function, so regenerate it.
        if not isinstance(instance, Header):
            header = None
        else:
            # If the header is undefined in the instance then don't try to
            # compute this function.
            header = instance.header
            if header is None:
                return None
        formatted_test = self.test if self.test else self.format_test(header)

        msg = 'checking %s' % self.name
        if header:
            msg += ' in %r' % header

        fbuild.logger.check(msg)

        # run the test
        try:
            stdout, stderr = instance.builder.tempfile_run(formatted_test,
                input=self.stdin,
                timeout=self.timeout)
        except fbuild.ExecutionError:
            fbuild.logger.failed()
        else:
            return self.process_stdout(stdout)

    def format_test(self, instance):
        raise NotImplementedError

    def process_stdout(self, stdout):
        raise NotImplementedError

    def __eq__(self, other):
        return \
            self.__class__ is other.__class__ and \
            self.__name__ == other.__name__ and \
            self.name == other.name and \
            self.test == other.test and \
            self.stdin == other.stdin and \
            self.stdout == other.stdout and \
            self.timeout == other.timeout

    def __hash__(self):
        return hash((
            self.__class__.__module__,
            self.__class__.__name__,
            self.__name__,
            self.name,
            self.test,
            self.stdin,
            self.stdout,
            self.timeout,
        ))

class function_test(AbstractFieldDescriptor):
    """L{function_test} is a descriptor that tests for the function on the
    first access. If it exists, an instance of L{Function} is memoized in the
    object and returned. Otherwise, memoize and return None."""

    def __init__(self, return_type, *args, default_args=None, **kwargs):
        super().__init__(**kwargs)
        self.return_type = return_type
        self.args = args
        self.default_args = default_args

    def format_definition(self):
        return '%s %s(%s)' % (
            self.return_type,
            self.name,
            ', '.join(self.args),
        )

    def format_call(self, args):
        return '%s(%s)' % (
            self.name,
            ', '.join(str(a) for a in args),
        )

    def format_test(self, header=None):
        if header is None:
            header = ''
        else:
            header = '#include <%s>' % header

        args = []
        defs = []

        if self.default_args:
            args = self.default_args
        else:
            for i, arg in enumerate(self.args):
                # we need to filter out void arguments
                if arg != 'void':
                    if isinstance(arg, Function):
                        args.append('%s (arg_%d)(%s)' % (
                            arg.return_type,
                            i,
                            ', '.join(arg.args)))
                        defs.append('%s arg_%d;' % (arg, i))
                    else:
                        args.append('arg_%d' % i)
                        defs.append('%s arg_%d;' % (arg, i))
        call = self.format_call(args)

        if self.return_type != 'void':
            call = '%s res = %s' % (self.return_type, call)

        return textwrap.dedent('''
            %s
            int main() {
                %s
                %s;
                return 0;
            }
        ''') % (header, '\n    '.join(defs), call)

    def process_stdout(self, stdout):
        if self.stdout is None or self.stdout == stdout:
            fbuild.logger.passed()
            return Function(self.return_type, *self.args)

        fbuild.logger.failed()

    def __eq__(self, other):
        return \
            super().__eq__(other) and \
            self.return_type == other.return_type and \
            self.args == other.args and \
            self.default_args == other.default_args

    def __hash__(self):
        return hash((
            super().__hash__(),
            self.return_type,
            self.args,
            self.default_args,
        ))

# ------------------------------------------------------------------------------

class macro_test(AbstractFieldDescriptor):
    """L{macro_test} is a descriptor that tests for the function on the first
    access. If it exists, an instance of L{Macro} is memoized in the object and
    returned. Otherwise, memoize and return None."""

    def format_test(self, header=None):
        if header is None:
            header = ''
        else:
            header = '#include <%s>' % header

        return textwrap.dedent('''
            %s
            #ifndef %s
            #error %s
            #endif
            int main() {
                return 0;
            }
        ''') % (header, self.name, self.name)

    def process_stdout(self, stdout):
        if self.stdout is None or self.stdout == stdout:
            fbuild.logger.passed()
            return Macro()

        fbuild.logger.failed()

# ------------------------------------------------------------------------------

class type_test(AbstractFieldDescriptor):
    """L{type_test} is a descriptor that tests for the function on the first
    access. If it exists, an instance of L{Type} is memoized in the object and
    returned. Otherwise, memoize and return None."""

    def format_test(self, header=None):
        return textwrap.dedent('''
            #include <stddef.h>
            #include <stdio.h>
            %s

            typedef %s type;
            struct TEST { char c; type mem; };
            int main() {
                printf("%%d\\n", (int)offsetof(struct TEST, mem));
                printf("%%d\\n", (int)sizeof(type));
                return 0;
            }
        ''') % ('' if header is None else '#include <%s>' % header, self.name)

    def process_stdout(self, stdout):
        stdout = stdout.split()
        alignment = int(stdout[0])
        size = int(stdout[1])

        fbuild.logger.passed('alignment: %s size: %s' % (alignment, size))

        return Type(alignment, size)

class int_type_test(AbstractFieldDescriptor):
    """L{int_type_test} is a descriptor that tests for the function on the
    first access.  If it exists, an instance of L{IntType} is memoized in the
    object and returned.  Otherwise, memoize and return None."""

    def format_test(self, header=None):
        return textwrap.dedent('''
            #include <stddef.h>
            #include <stdio.h>
            %s

            typedef %s type;
            struct TEST { char c; type mem; };
            int main() {
                printf("%%d\\n", (int)offsetof(struct TEST, mem));
                printf("%%d\\n", (int)sizeof(type));
                printf("%%d\\n", (type)~3 < (type)0);
                return 0;
            }
        ''') % ('' if header is None else '#include <%s>' % header, self.name)

    def process_stdout(self, stdout):
        stdout = stdout.split()
        alignment = int(stdout[0])
        size = int(stdout[1])
        signed = int(stdout[2]) == 1

        fbuild.logger.passed('alignment: %s size: %s signed: %s' %
            (alignment, size, signed))

        return IntType(alignment, size, signed)

# ------------------------------------------------------------------------------

class struct_test(AbstractFieldDescriptor):
    """L{struct_test} is a descriptor that tests for the function on the first
    access.  If it exists, an instance of L{Struct} is memoized in the object
    and returned.  Otherwise, memoize and return None."""

    def __init__(self, *members, **kwargs):
        super().__init__(**kwargs)
        self.members = members

    def contribute_to_class(self, cls, key):
        self.__name__ = key
        if self.name is None:
            self.name = 'struct ' + key
        cacheproperty(self).contribute_to_class(cls, key)

    def format_test(self, header=None):
        if header is None:
            header = ''
        else:
            header = '#include <%s>' % header

        defs = []
        for i, (type, member) in enumerate(self.members):
            defs.append('%s arg_%d = arg.%s;' % (type, i, member))

        return textwrap.dedent('''
            %s
            int main() {
                %s arg;
                %s
                return 0;
            }
        ''') % (header, self.name, '\n    '.join(defs))

    def process_stdout(self, stdout):
        if self.stdout is None or self.stdout == stdout:
            fbuild.logger.passed()
            return Struct(*self.members)

        fbuild.logger.failed()

    def __eq__(self, other):
        return \
            super().__eq__(other) and \
            self.members == other.members

    def __hash__(self):
        return hash((
            super().__hash__(),
            self.members,
        ))

# ------------------------------------------------------------------------------

class variable_test(AbstractFieldDescriptor):
    """L{variable_test} is a descriptor that tests for the function on the
    first access.  If it exists, an instance of L{Variable} is memoized in the
    object and returned.  Otherwise, memoize and return None."""

    def format_test(self, header=None):
        if header is None:
            header = ''
        else:
            header = '#include <%s>' % header

        return textwrap.dedent('''
            %s
            int main() {
                %s;
                return 0;
            }
        ''') % (header, self.name)

    def process_stdout(self, stdout):
        if self.stdout is None or self.stdout == stdout:
            fbuild.logger.passed()
            return Variable()

        fbuild.logger.failed()

# ------------------------------------------------------------------------------

class Test(fbuild.config.Test):
    def __init__(self, builder):
        self.builder = builder

    def fields(self):
        for field in self.__meta__.fields:
            type_ = getattr(self, field.__name__)
            yield field.method.name, type_

    def functions(self):
        for name, field in self.fields():
            if isinstance(field, Function):
                yield name, field

    def macros(self):
        for name, field in self.fields():
            if isinstance(field, Macro):
                yield name, field

    def types(self):
        for name, field in self.fields():
            if isinstance(field, Type):
                yield name, field

    def int_types(self):
        for name, field in self.fields():
            if isinstance(field, IntType):
                yield name, field

    def structs(self):
        for name, field in self.fields():
            if isinstance(field, Struct):
                yield name, field

    def variables(self):
        for name, field in self.fields():
            if isinstance(field, Variable):
                yield name, field

# ------------------------------------------------------------------------------

class HeaderMeta(fbuild.config.TestMeta):
    def __new__(cls, name, bases, attrs):
        filename = attrs.pop('header', None)

        new_class = super().__new__(cls, name, bases, attrs)

        # Don't do anything if haven't instantiated HeaderMeta yet.
        if not any(isinstance(base, HeaderMeta) for base in bases):
            return new_class

        # Create a header property that will dynamically evaluate the header
        # when it's accessed.  If the header name wasn't specified, default to
        # replacing the last '_' in the filename with a '.'.
        if filename is None:
            filename = '.'.join(name.rsplit('_', 1))

        def header(self):
            if self.builder.check_header_exists(filename):
                return filename
            return None
        new_class.header = cacheproperty(header)

        return new_class

class Header(Test, metaclass=HeaderMeta):
    # This will be converted into a property in the metaclass.
    header = None

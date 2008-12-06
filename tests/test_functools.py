import unittest

from fbuild.functools import *

# -----------------------------------------------------------------------------

class TestFunctionBind(unittest.TestCase):
    def testUnary(self):
        def f():
            pass

        self.assertEquals(bind_args(f, (), {}), {})

        self.assertRaises(TypeError, bind_args, f, (1,), {})
        self.assertRaises(TypeError, bind_args, f, (),   {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})

    def testSingle(self):
        def f(a):
            pass

        self.assertEquals(bind_args(f, (1,), {}),     {'a': 1})
        self.assertEquals(bind_args(f, (2,), {}),     {'a': 2})
        self.assertEquals(bind_args(f, (), {'a': 3}), {'a': 3})

        self.assertRaises(TypeError, bind_args, f, (),     {})
        self.assertRaises(TypeError, bind_args, f, (1, 2), {})
        self.assertRaises(TypeError, bind_args, f, (),     {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,),   {'x':1})


    def testMultiple(self):
        def f(a, b, c):
            pass

        self.assertEquals(bind_args(f, (1, 2, 3), {}), dict(a=1, b=2, c=3))
        self.assertEquals(bind_args(f, (2, 3, 4), {}), dict(a=2, b=3, c=4))

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2, 'c': 3}),
            dict(a=1, b=2, c=3))

        self.assertEquals(
            bind_args(f, (1,), {'b': 2, 'c': 3}),
            dict(a=1, b=2, c=3))

        self.assertEquals(
            bind_args(f, (1, 2), {'c': 3}),
            dict(a=1, b=2, c=3))

        self.assertRaises(TypeError, bind_args, f, (),           {})
        self.assertRaises(TypeError, bind_args, f, (1, 2),       {})
        self.assertRaises(TypeError, bind_args, f, (1, 2, 3, 4), {})
        self.assertRaises(TypeError, bind_args, f, (),           {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,),         {'x':1})

    def testDefault(self):
        def f(a, b, c=8, d=9):
            pass

        self.assertEquals(
            bind_args(f, (1, 2), {}),
            dict(a=1, b=2, c=8, d=9))

        self.assertEquals(
            bind_args(f, (1, 2, 4), {}),
            dict(a=1, b=2, c=4, d=9))

        self.assertEquals(
            bind_args(f, (1, 2, 3, 4), {}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2, 'c': 3, 'd': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1,), {'b': 2, 'c': 3, 'd': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1, 2), {'c': 3, 'd': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1, 2, 3), {'d': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertRaises(TypeError, bind_args, f, (),              {})
        self.assertRaises(TypeError, bind_args, f, (1,),            {})
        self.assertRaises(TypeError, bind_args, f, (1, 2, 3, 4, 5), {})
        self.assertRaises(TypeError, bind_args, f, (),              {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,),            {'x':1})

    def testVarArgs0(self):
        def f(*args):
            pass

        self.assertEquals(bind_args(f, (), {}),        {})
        self.assertEquals(bind_args(f, (1, 2, 4), {}), {'args': (1, 2, 4)})

        self.assertRaises(TypeError, bind_args, f, (),   {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})

    def testVarArgs1(self):
        def f(a, *args):
            pass

        self.assertEquals(bind_args(f, (1,), {}),      dict(a=1))
        self.assertEquals(bind_args(f, (), {'a': 1}),  dict(a=1))
        self.assertEquals(bind_args(f, (1, 2, 4), {}), dict(a=1, args=(2, 4)))

        self.assertRaises(TypeError, bind_args, f, (),   {})
        self.assertRaises(TypeError, bind_args, f, (2, 4), {'a': 1})
        self.assertRaises(TypeError, bind_args, f, (),   {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})

    def testVarArgs2(self):
        def f(a, b, c=8, d=9, *args):
            pass

        self.assertEquals(
            bind_args(f, (1, 2), {}),
            dict(a=1, b=2, c=8, d=9))

        self.assertEquals(
            bind_args(f, (1, 2, 4), {}),
            dict(a=1, b=2, c=4, d=9))

        self.assertEquals(
            bind_args(f, (1, 2, 3, 4), {}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1, 2, 3, 4, 5), {}),
            dict(a=1, b=2, c=3, d=4, args=(5,)))

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2, 'c': 3, 'd': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1,), {'b': 2, 'c': 3, 'd': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1, 2), {'c': 3, 'd': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertEquals(
            bind_args(f, (1, 2, 3), {'d': 4}),
            dict(a=1, b=2, c=3, d=4))

        self.assertRaises(TypeError, bind_args, f, (),   {})
        self.assertRaises(TypeError, bind_args, f, (1,), {})
        self.assertRaises(TypeError, bind_args, f, (),   {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})
        self.assertRaises(TypeError, bind_args, f,
            (1, 2, 3, 4, 5), {'a': 1, 'b': 2, 'c': 3, 'd': 4})

    def testKeywordOnly(self):
        def f(*, a, b):
            pass

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2}),
            dict(a=1, b=2))

        self.assertRaises(TypeError, bind_args, f, (),   {})
        self.assertRaises(TypeError, bind_args, f, (1,), {})
        self.assertRaises(TypeError, bind_args, f, (),   {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})

    def testKeywordDefaults(self):
        def f(*, a, b=8, c=9):
            pass

        self.assertEquals(
            bind_args(f, (), {'a': 1}),
            dict(a=1, b=8, c=9))

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2, 'c': 3}),
            dict(a=1, b=2, c=3))

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2}),
            dict(a=1, b=2, c=9))

        self.assertRaises(TypeError, bind_args, f, (1,), {})
        self.assertRaises(TypeError, bind_args, f, (),   {'x':1})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})

    def testVarKeyword0(self):
        def f(**kwargs):
            pass

        self.assertEquals(bind_args(f, (), {}),       {})
        self.assertEquals(bind_args(f, (), {'a': 1}), {'a':1})

        self.assertEquals(
            bind_args(f, (), {'a': 1, 'b': 2, 'c': 3}),
            dict(a=1, b=2, c=3))

        self.assertRaises(TypeError, bind_args, f, (1,), {})
        self.assertRaises(TypeError, bind_args, f, (1,), {'x':1})

    def testAll(self):
        def f(a, b, c=7, d=8, *args, e, f, g=9, h=0, **kwargs):
            pass

        self.assertEquals(
            bind_args(f, (1, 2), {'e': 3, 'f': 4}),
            dict(a=1, b=2, c=7, d=8, e=3, f=4, g=9, h=0))

        self.assertEquals(
            bind_args(f, (1, 2, 3, 4, 5), dict(e=3, f=4, g=5, h=6, i=7)),
            dict(a=1, b=2, c=3, d=4, e=3, f=4, g=5, h=6, i=7, args=(5,)))

# -----------------------------------------------------------------------------

def suite(*args, **kwargs):
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFunctionBind)

    return suite

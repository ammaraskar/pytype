"""Test cases that need solve_unknowns."""

import unittest

from pytype.tests import test_inference


class SolverTests(test_inference.InferenceTest):
  """Tests for type inference that also runs convert_structural.py."""

  def testAmbiguousAttr(self):
    with self.Infer("""
      class Node(object):
          children = ()
          def __init__(self):
              self.children = []
              for ch in self.children:
                  pass
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
      class Node:
        children: list<nothing> or tuple<nothing>
        def __init__(self) -> NoneType
      """)

  def testCall(self):
    with self.Infer("""
      def f():
        x = __any_object__
        y = x.foo
        z = y()
        eval(y)
        return z
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def f() -> ?
      """)

  def testTypeParameters(self):
    with self.Infer("""
      def f(A):
        return [a - 42.0 for a in A.values()]
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, (
          "def f(A: dict<?, complex or dict_keys<?> or float>) -> "
          "list<complex or float or set<?>>"))

  def testAnythingTypeParameters(self):
    with self.Infer("""
      def f(x):
        return x.keys()
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def f(x: dict<?, ?>) -> list<?>
      """)

  def testNameConflict(self):
    with self.Infer("""
      import StringIO

      class Foobar(object):
        def foobar(self, out):
          out.write('')

      class Barbaz(object):
        def barbaz(self):
          __any_object__.foobar(StringIO.StringIO())
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
        StringIO: module

        class Foobar(object):
          def foobar(self, out: file) -> NoneType

        class Barbaz(object):
          def barbaz(self) -> NoneType
      """)

  def testTopLevelClass(self):
    with self.Infer("""
      import Foo

      class Bar(Foo):
        pass
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
        Foo: ?

        class Bar(?):
          pass
      """)

  def testDictWithNothing(self):
    with self.Infer("""
      def f():
        d = {}
        d[1] = "foo"
        for name in d:
          len(name)
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def f() -> NoneType
      """)

  @unittest.skip("Broken. We need to generate tuple<?> in infer.py.")
  def testOptionalParams(self):
    with self.Infer("""
      class Foo(object):
        def __init__(self, *types):
          self.types = types
        def bar(self, val):
          return isinstance(val, self.types)
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
      class Foo(object):
        types: tuple<?>
        def __init__(self, ...) -> NoneType
        def bar(self, val) -> bool
      """)

if __name__ == "__main__":
  test_inference.main()

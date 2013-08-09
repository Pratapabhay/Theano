import numpy as np

from theano.scalar.basic import Apply, ScalarOp, as_scalar, float64, float32, int64
from theano.gof.utils import remove

imported_sympy = False
try:
    import sympy
    from sympy.utilities.codegen import get_default_datatype, codegen
    imported_sympy = True
except ImportError:
    pass

import itertools as it

names = ("sympy_func_%d"%i for i in it.count(0))

def include_line(line):
    return '#include' in line

def sympy_dtype(expr):
    return get_default_datatype(expr).cname
def theano_dtype(expr):
    return {'double': float64,
            'float': float32,
            'int': int64}[sympy_dtype(expr)]

class SymPyCCode(ScalarOp):
    """ An Operator that wraps SymPy's C code generation

    >>> from sympy.abc import x, y  # SymPy Variables
    >>> from theano.scalar.basic_sympy import SymPyCCode
    >>> op = SymPyCCode([x, y], x + y)

    >>> from theano.scalar.basic import floats
    >>> xt, yt = floats('xy') # Theano variables
    >>> zt = op(xt, yt)

    >>> import theano
    >>> f = theano.function([xt, yt], zt)
    >>> f(1.0, 2.0)
    3.0
    """


    def __init__(self, inputs, expr, name=None):
        self.name = name or next(names)
        self.inputs = inputs
        self.expr = expr

    def c_support_code(self):
        [(c_name, c_code), (h_name, c_header)] = codegen(
                (self.name, self.expr), 'C', 'project_name',
                header=False, argument_sequence=self.inputs)
        return '\n'.join(remove(include_line, c_code.split('\n')))

    def c_code(self, node, name, input_names, output_names, sub):
        y, = output_names
        xs = ', '.join(input_names)
        f = self.name
        return "%(y)s = %(f)s(%(xs)s);" % locals()

    def output_types_preference(self, *inputs):
        return [theano_dtype(self.expr)]

    def make_node(self, *inputs):
        # TODO: assert input types are correct use get_default_datatype

        if len(inputs) != len(self.inputs):
            raise TypeError("Wrong number of inputs for %s.make_node (got %i(%s), expected %i)" % (self, len(inputs), str(inputs), self.nin))

        inputs = [as_scalar(input) for input in inputs]
        outputs = [t() for t in self.output_types([input.type for input in inputs])]
        return Apply(self, inputs, outputs)

    def perform(self, node, inputs, output_storage):
        raise NotImplementedError()

    def _info(self):
        return type(self), self.name, tuple(self.inputs), self.expr

    def __eq__(self, other):
        return type(self) == type(other) and self._info() == other._info()

    def __hash__(self):
        return hash(self._info())

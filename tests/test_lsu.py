from pysat.examples.lsu import LSU
from pysat.formula import WCNF


def test_get_model_returns_reusable_list():
    formula = WCNF()
    formula.append([1], weight=1)

    with LSU(formula, solver='g3') as lsu:
        assert lsu.solve() is True

        model = lsu.get_model()

        assert isinstance(model, list)
        assert lsu.get_model() == model

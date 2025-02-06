
from jumpstarter_driver_composite.driver import Composite

from jumpstarter.driver import Driver


def test_composite_basic():
    class SimpleDriver(Driver):
        @classmethod
        def client(cls) -> str:
            return "test.client.SimpleClient"

    child1 = SimpleDriver()
    child2 = SimpleDriver()

    composite = Composite(children={
        "child1": child1,
        "child2": child2
    })

    assert len(composite.children) == 2
    assert composite.children["child1"] == child1
    assert composite.children["child2"] == child2

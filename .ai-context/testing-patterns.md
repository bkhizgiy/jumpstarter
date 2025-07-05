# Patterns for Testing Jumpstarter

Testing Jumpstarter itself can be complex due to the inherit difficulties of
testing a framework that is designed to help with testing hardware.

## Testing Conventions

### Jumpstarter Testing Rules

- Test files are named as `*_test.py` based on the file under test.
  - For example, tests for `drivers.py` would be `drivers_test.py`.
- All tests are written using `pytest`
- We use `anyio` to mark `async` tests
  - If the entire file is async tests, use `pytestmark = pytest.mark.anyio`
  - If just a single test is async, use the `@pytest.mark.anyio` decorator
- Test should be organized as appropriate:
  - Simple tests cases are written as functions prefixed with `test_`, for example `def test_http_server():`
  - For more complex tests, use test classes to better organize test cases with the prefix `Test`, for example `class TestClusterCreation:`
- We use patching to mock modules that are not under test
  - For new tests, we prefer to use `unittest.mock`. For example, `@patch("jumpstarter_cli_admin.install.get_minikube_ip")`

### Running Tests

- To run tests for a specific package run: `make pkg-test-<pkg>`
- To run tests for all packages run: `make pkg-test-all`
- To run documentation tests run: `make docs-test`
- To run all documentation and package tests run: `make test`

## Test Types

Depending on the type of package under test, we use different testing styles.

### Jumpstarter Core

The core `jumpstarter` package can be tested using unit tests on each of its components. Typically, these are simple tests to exercise the functionality of the core library.

Here is an example test case for the core library:

```python
import pytest

from .importlib import import_class


def test_import_class():
    import_class("os.open", [], True)

    with pytest.raises(ImportError):
        import_class("os.invalid", [], True)

    with pytest.raises(ImportError):
        import_class("os.open", [], False)

    import_class("os.open", ["os.*"], False)

    with pytest.raises(ImportError):
        import_class("os.open", ["sys.*"], False)

    with pytest.raises(ImportError):
        import_class("os", [], True)

```

### Jumpstarter Drivers

Driver packages start with `jumpstarter-driver-*`.

To test drivers we can use several utility functions from the `jumpstarter.common.utils` module.

To test creating a driver and instantiating the correct client class, we can use the `serve` function.

Here is an example using `serve` to test a driver class:

```python
from jumpstarter.common.utils import serve

from .driver import ExampleDriver

def test_driver_example():
    instance = ExampleDriver(my_argument=True)

    with serve(instance) as client:
        assert client.example() == 1
```

To test a driver client CLI, we can use Click's built-in testing capabilities with `CliRunner`.

```python

```

### Jumpstarter CLI

CLI packages start with `jumpstarter-cli-*`.

To test the Jumpstarter CLI packages such as `jumpstarter-cli-admin`, we can use Click's built-in testing capabilities with the `CliRunner`.

Here is an example test for a CLI:

```python
from click.testing import CliRunner

from . import cli


def test_cli_list():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["list"],
    )
    assert result.exit_code == 0
```

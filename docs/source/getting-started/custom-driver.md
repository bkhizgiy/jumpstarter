# Custom Driver
To use hardware interfaces not supported by jumpstarter provided drivers, we can write custom drivers. Every jumpstarter drivers takes the form of two python classes, one for the exporter side, another for the client side.

## Writing Driver
A custom driver allowing you to run arbitrary commands on the exporter would look like this.
```python
# jumpstarter_custom_driver/__init__.py
from jumpstarter.driver import Driver, export
from jumpstarter.client import DriverClient

# exporter side
class CustomDriver(Driver):
    # required method returning the import path of the client class
    @classmethod
    def client(cls) -> str:
        return "jumpstarter_custom_driver.CustomClient"

    @export # export the method to make it available from the client
    def execute(self, command: str, args: list[str]) -> str: # only positional arguments
        result = run_command(command, args) # run the command in shell, etc.
        return result

# client side
class CustomClient(DriverClient):
    def execute(self, command: str, args: list[str]) -> str:
        # self.call is provided by the DriverClient base class
        # which can be used to transparently call exporter side methods by name
        # the parameters and return values are serialized with protobuf
        # so make sure to only use simple types like list/dict
        return self.call("execute", command, args)

    # additional helper methods can also be provided
    def ls(self) -> str:
        return self.execute("ls", [])

    def rm(self, files: list[str]) -> str:
        return self.execute("rm", files)
```

## Installing Driver
The driver should be distributed as a python package, and installed on both the exporters and the clients.
```toml
# pyproject.toml
[project]
name = "jumpstarter-custom-driver"
version = "0.0.1"
dependencies = [
  "jumpstarter",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Using Driver
Custom drivers can be used in the same way as jumpstarter provided drivers.
```yaml
# /etc/jumpstarter/exporters/custom.yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
endpoint: ""
token: ""
export:
    custom:
        # full import path of the driver class
        type: jumpstarter_driver_custom.CustomDriver
```

## Advanced Driver
Drivers can also take configuration parameters, export generator methods, async methods or TCP like byte streams. For writing advanced drivers using these features, please refer to [Driver API Reference](#driver-api)

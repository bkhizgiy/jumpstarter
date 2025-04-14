import time
from typing import Any, Callable, Generator, Optional

from robot.api import Error, logger
from robot.api.deco import library

from jumpstarter.common.utils import env
from jumpstarter.config import ClientConfigV1Alpha1


@library(scope="GLOBAL", version="0.6.0", listener="JumpstarterLibraryListener")
class JumpstarterLibrary:
    """A Robot Framework library for interacting with Jumpstarter devices.

    This library provides dynamic keywords for controlling Jumpstarter devices through
    the Robot Framework. Keywords are generated from the driver clients.

    Example:
        *** Settings ***
        Library    jumpstarter_robotframework.JumpstarterLibrary    selector=example.com/board=qemu

        *** Test Cases ***
        Example Test
            Dutlink Power On
            Dutlink Storage Write Local File    /path/to/image.img
            Dutlink Storage Connect To DUT
            Dutlink Power Off
            Release Lease
    """

    _selector: Optional[str] = None
    _client_alias: Optional[str] = None
    _exporter_config: Optional[str] = None
    _client: Any = None
    _lease: Any = None

    def __init__(
        self, selector: Optional[str] = None, client: Optional[str] = None, exporter_config: Optional[str] = None
    ):
        """Initialize the library with the specified selector and client alias.

        If a selector is provided, the lease will be automatically acquired when the
        test suite begins. Otherwise, the "Acquire Lease" keyword must be used to
        manually acquire the lease. Leases are automatically released when the test
        suite ends or when the "Release Lease" keyword is called. Multiple leases can
        be acquired by calling the "Acquire Lease" keyword multiple times.

        Args:
            selector: Optional selector string to identify the device.
            client: Optional client alias to use a specific client config.
            exporter_config: Optional exporter config file path to use a local exporter for testing and intellisense.
        """
        self._selector = selector
        self._client_alias = client
        self._exporter_config = exporter_config

    def _acquire_lease(self, selector: str, client_alias: Optional[str] = None):
        """Acquire a lease for the Jumpstarter device."""
        # If the lease is already acquired, throw an error
        if self._lease is not None:
            raise Error("Lease already acquired")

        try:
            # Use the existing environment if running in the Jumpstarter shell
            with env() as client:
                self._client = client
        except RuntimeError:
            # Otherwise, manually acquire a lease
            try:
                config = ClientConfigV1Alpha1.load(alias=client_alias or "default")
                self._lease = config.lease(selector=selector)
                self._client = self._lease.__enter__()
            except Exception as e:
                raise Error(f"Failed to acquire lease: {str(e)}") from e

    def _release_lease(self) -> None:
        """Release the lease for the Jumpstarter device."""
        if self._lease is None:
            logger.warn("No lease to release, skipping")
            return

        try:
            self._lease.__exit__(None, None, None)
        except Exception as e:
            raise Error(f"Failed to release lease: {str(e)}") from e
        self._lease = None
        self._client = None
        # BUG workaround: make sure that grpc servers get the client/lease release properly
        time.sleep(1)

    def acquire_lease(self, selector: str, client: Optional[str] = None) -> None:
        """Acquire a lease for the Jumpstarter device.

        This keyword acquires a lease for the device. It is automatically called at the
        start of the test suite if a selector was provided during library initialization,
        but can be called manually if needed.

        Example:
            Acquire Lease    selector=example.com/board=qemu
        """
        if self._lease is not None:
            raise Error("Lease already acquired")

        self._selector = selector
        self._client_alias = client
        self._acquire_lease(selector=selector, client_alias=client)

    def release_lease(self) -> None:
        """Release the lease for the Jumpstarter device.

        This keyword releases the lease acquired for the device. It is automatically
        called at the end of the test suite, but can be called manually if needed.

        Example:
            Release Lease
        """
        self._release_lease()

    def _get_nested_keywords(self, obj: Any, prefix: str = "") -> Generator[str, None, None]:
        """Recursively get all keyword names from nested objects.

        This method concatenates the full path to the driver client method with underscores
        to follow the Robot Framework keyword naming convention.

        Args:
            obj: The object to introspect
            prefix: Current prefix for nested keywords
        """
        # Ignore objects that are not callable
        if obj is None:
            return

        for attr_name in dir(obj):
            # Ignore private attributes
            if attr_name.startswith("_"):
                continue

            # Get the attribute metadata
            attr = getattr(obj, attr_name)
            # Concatenate the prefix with the attribute name to form the full keyword name
            full_name = f"{prefix}_{attr_name}" if prefix else attr_name

            # If it's a callable keyword method, yield the full name
            if callable(attr):
                yield full_name
            # If it's an object, recursively get its keywords
            elif hasattr(attr, "__dict__") or hasattr(attr, "__slots__"):
                yield from self._get_nested_keywords(attr, full_name)

    def _get_client(self) -> Any:
        """Get the client object, acquiring a lease if needed.

        Returns:
            The client object

        Raises:
            Error: If no lease has been acquired and no selector was provided
        """
        # If we already have a client, return it
        if self._client is not None:
            return self._client

        # If we have a selector but no lease, try to acquire the lease
        if self._lease is None and self._selector is not None:
            self._acquire_lease(selector=self._selector, client_alias=self._client_alias)

        # Check if we now have a client
        if self._client is None:
            raise Error(
                "No lease acquired. You must call 'Acquire Lease', provide a selector in the library settings, "
                "or specify an exporter_config for local testing."
            )

        # Return the client object
        return self._client

    def get_keyword_names(self) -> Generator[str, None, None]:
        """Get all available keyword names.

        This method returns both static keywords defined in this class and
        dynamic keywords from the client object and its nested objects.
        """
        # Static keywords
        yield "acquire_lease"
        yield "release_lease"

        # Dynamic keywords from client object and its nested objects
        try:
            current = self._get_client()
        except Error:
            logger.warn("Unable to acquire lease, skipping dynamic keywords")
            return

        # Get the keywords from the client object and its nested objects
        yield from self._get_nested_keywords(current)

    def __getattr__(self, name: str) -> Callable:
        """Dynamically create keyword methods from the client object.

        This method is called when a keyword is not found in the static
        keywords. It creates a wrapper around the client method and
        makes it available as a Robot Framework keyword.

        Args:
            name: The name of the keyword to create

        Raises:
            Error: If no lease has been acquired or if the attribute can't be found
        """
        # Handle static keywords first
        if name == "acquire_lease":
            return self.acquire_lease
        if name == "release_lease":
            return self.release_lease

        # If we don't have a client, raise an error
        if self._client is None:
            raise Error(
                "No lease acquired. You must call 'Acquire Lease', provide a selector in the library settings, "
                "or specify an exporter_config for local testing."
            )

        # Track the current object as we navigate through the hierarchy
        obj = self._client

        # Split the name into parts to navigate the object hierarchy
        parts = name.split("_")

        # Track the remaining parts to check
        remaining_parts = parts[:]

        # Keep navigating through the object hierarchy
        while remaining_parts:
            # Try to find a path through the object hierarchy
            for i in range(1, len(remaining_parts) + 1):
                # Construct possible attribute name from the first i parts
                attr_name = "_".join(remaining_parts[:i])

                # Check if this attribute exists
                if hasattr(obj, attr_name):
                    # Found an attribute, move to it
                    obj = getattr(obj, attr_name)
                    # Remove the parts we've processed
                    remaining_parts = remaining_parts[i:]
                    break
            else:
                # If we didn't find any valid attribute, raise an error
                raise Error(f"Cannot find attribute in path: {name}")

            # If we've navigated to a callable and there are no more parts, we're done
            if not remaining_parts and callable(obj):
                return obj

        # If we got here without finding a callable, it's an error
        raise Error(f"Attribute '{name}' is not callable")


class JumpstarterLibraryListener:
    """Listener for the JumpstarterLibrary that handles lease management."""

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, library: JumpstarterLibrary) -> None:
        """Initialize the listener with a reference to the library.

        Args:
            library: The JumpstarterLibrary instance
        """
        self.library = library

    def start_suite(self, suite, result) -> None:
        """Called at the start of the test suite.

        This method is automatically called by Robot Framework when the test suite begins.
        It acquires the lease if a selector was provided.

        Args:
            suite: The test suite object
            result: The test suite result object
        """
        if self.library._selector is not None:
            logger.info("Automatically acquiring Jumpstarter lease at the start of the test suite")
            self.library._acquire_lease(selector=self.library._selector, client_alias=self.library._client_alias)

    def end_suite(self, suite, result) -> None:
        """Called at the end of the test suite.

        This method is automatically called by Robot Framework when the test suite ends.
        It releases the lease if one was acquired.

        Args:
            suite: The test suite object
            result: The test suite result object
        """
        if self.library._lease is not None:
            logger.info("Automatically releasing Jumpstarter lease at the end of the test suite")
            self.library._release_lease()

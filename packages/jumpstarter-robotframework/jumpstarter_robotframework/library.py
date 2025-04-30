import os
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Callable, Generator, Optional

from robot.api import Error, logger
from robot.api.deco import library
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError  # type: ignore

from jumpstarter.client.base import DriverClient
from jumpstarter.client.lease import Lease
from jumpstarter.common.importlib import import_class
from jumpstarter.common.utils import env
from jumpstarter.config.client import ClientConfigV1Alpha1
from jumpstarter.config.exporter import (
    ExporterConfigV1Alpha1,
    ExporterConfigV1Alpha1DriverInstance,
    ExporterConfigV1Alpha1DriverInstanceBase,
    ExporterConfigV1Alpha1DriverInstanceComposite,
)


@library(scope="GLOBAL", version="0.6.0")
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
    _client: Optional[Any] = None
    _lease: Optional[Lease] = None
    _portal: Any = None
    _stack: ExitStack
    _unix_socket_path: Optional[Path] = None
    _builtin: Optional[BuiltIn] = None
    _stub_client: Optional[Any] = None

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
        self.ROBOT_LIBRARY_LISTENER = JumpstarterLibraryListener(self)
        self._selector = selector
        self._client_alias = client
        self._exporter_config = exporter_config
        self._stack = ExitStack()
        self._stub_client = None

        # Initialize BuiltIn instance once
        try:
            self._builtin = BuiltIn()
        except RobotNotRunningError:
            self._builtin = None
            logger.warn("Robot Framework is not running")

        # If we're not running a test suite, create a stub client for documentation/intellisense
        # if not self._is_robot_running() and self._exporter_config:
        #     logger.debug("Creating stub client from exporter config")
        #     self._create_stub_client()

    def get_client_keywords(self, exporter: ExporterConfigV1Alpha1) -> Generator[str, None, None]:
        """Create a list of keywords by analyzing the exporter configuration.

        This method performs static analysis on the exporter configuration to generate
        a list of available keywords. It traverses the driver tree structure and
        extracts method names from each driver's client class.

        Args:
            exporter: The exporter configuration to analyze

        Yields:
            str: Available keywords in the format 'driver_name_method_name'
        """

        def get_client_methods(driver_type: str) -> set[str]:
            """Get all public methods from a driver's client class."""
            try:
                driver_class = import_class(driver_type, allow=[], unsafe=True)
                client_class_name = driver_class.client()
                client_class = import_class(client_class_name, allow=[], unsafe=True)
                base_methods = set(dir(DriverClient))
                return {
                    name
                    for name in dir(client_class)
                    if callable(getattr(client_class, name))
                    and not name.startswith("_")
                    and name != "cli"
                    and name not in base_methods
                }
            except Exception as e:
                raise Error(f"Error getting client methods for {driver_type}: {e}") from e

        def process_driver(
            name: str, driver: ExporterConfigV1Alpha1DriverInstance, prefix: str = ""
        ) -> Generator[str, None, None]:
            """Recursively process a driver and its children to generate keywords."""
            # Get the driver type and its methods
            if isinstance(driver.root, ExporterConfigV1Alpha1DriverInstanceBase):
                logger.warn(f"Processing ExporterConfigV1Alpha1DriverInstanceBase driver: {name}")
                driver_type = driver.root.type
                logger.warn(f"Driver type: {driver_type}")
                methods = get_client_methods(driver_type)
                # Add keywords for this driver's methods
                for method in methods:
                    keyword = f"{prefix}{name}_{method}" if prefix else f"{name}_{method}"
                    yield keyword

                # Process children recursively
                for child_name, child in driver.root.children.items():
                    new_prefix = f"{prefix}{name}_" if prefix else f"{name}_"
                    yield from process_driver(child_name, child, new_prefix)

            elif isinstance(driver.root, ExporterConfigV1Alpha1DriverInstanceComposite):
                logger.warn(f"Processing ExporterConfigV1Alpha1DriverInstanceComposite driver: {name}")
                # Process all children of a composite driver
                for child_name, child in driver.root.children.items():
                    new_prefix = f"{prefix}{name}_" if prefix else f"{name}_"
                    yield from process_driver(child_name, child, new_prefix)

        # Process all top-level drivers
        for name, driver in exporter.export.items():
            logger.warn(f"Processing driver: {name}")
            yield from process_driver(name, driver)

    def _acquire_lease(
        self, selector: Optional[str] = None, client_alias: Optional[str] = None, exporter_config: Optional[str] = None
    ):
        """Acquire a lease for the Jumpstarter device."""
        if self._lease is not None or self._client is not None:
            raise Error("Lease already acquired")

        if exporter_config:
            logger.debug("acquire_lease: creating local exporter")
            try:
                config = ExporterConfigV1Alpha1.load(exporter_config)
                logger.debug("acquire_lease: serving unix socket")
                self._unix_socket_path = self._stack.enter_context(config.serve_unix())
                os.environ["JUMPSTARTER_HOST"] = str(self._unix_socket_path)
                os.environ["JMP_DRIVERS_ALLOW"] = "UNSAFE"  # Allow unsafe drivers for testing locally
                logger.debug(f"acquire_lease: unix socket path: {self._unix_socket_path}")
                logger.info(f"Successfully created local exporter using config: {exporter_config}")
            except Exception as e:
                self._release_lease()
                raise Error(f"Failed to create local exporter: {str(e)}") from e

        try:
            logger.debug("acquire_lease: entering env")
            self._client = self._stack.enter_context(env())
            logger.debug("acquire_lease: entered env")
        except RuntimeError:
            try:
                client_config = ClientConfigV1Alpha1.load(alias=client_alias or "default")
                self._lease = self._stack.enter_context(client_config.lease(selector=selector))
                self._client = self._stack.enter_context(self._lease.connect())
            except Exception as e:
                self._release_lease()
                raise Error(f"Failed to acquire lease: {str(e)}") from e

    def _release_lease(self) -> None:
        """Release the lease for the Jumpstarter device."""
        if self._lease is None and self._client is None:
            logger.info("No lease to release, skipping")
            return

        # Exit the ExitStack to release all resources
        self._stack.close()

        self._lease = None
        self._client = None

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

    def _get_nested_keywords(self, children: dict[str, DriverClient], prefix: str = "") -> Generator[str, None, None]:
        """Recursively get all keyword names from nested objects."""
        for key, child in children.items():
            # Get all methods from the child's class
            child_class = child.__class__

            # Get all methods from the class, including inherited ones except from DriverClient
            methods = {
                name: method
                for name, method in vars(child_class).items()
                if callable(method)  # Ensure that it is a callable method
                and not name.startswith("_")  # Exclude private methods
                and name != "cli"  # Exclude special cli method
                and not method.__qualname__.startswith("DriverClient")  # Exclude DriverClient methods
            }

            # Generate keyword names for this child's methods
            for method_name in methods:
                keyword_name = f"{prefix}_{key}_{method_name}" if prefix else f"{key}_{method_name}"
                logger.debug(f"get_nested_keywords: keyword_name: {keyword_name}")
                yield keyword_name

            # Recursively process nested children
            if hasattr(child, "children"):
                new_prefix = f"{prefix}_{key}" if prefix else key
                yield from self._get_nested_keywords(child.children, new_prefix)

    def _get_client(self) -> DriverClient:
        """Get the client object, acquiring a lease if needed.

        Returns:
            The client object

        Raises:
            Error: If no lease has been acquired and no selector was provided
        """
        # If we already have a client, return it
        if self._client is not None:
            logger.debug("get_client: returning existing client")
            return self._client

        # Otherwise, try to acquire a lease normally
        if self._lease is None:
            logger.debug("get_client: acquiring lease")
            self._acquire_lease(
                selector=self._selector, client_alias=self._client_alias, exporter_config=self._exporter_config
            )

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

        logger.warn("Discovered keywords:")
        for keyword in self.get_client_keywords(ExporterConfigV1Alpha1.load(self._exporter_config)):
            logger.warn(f"  {keyword}")

        # Dynamic keywords from client object and its nested objects
        try:
            client = self._get_client()
        except Error as e:
            logger.info(f"Unable to get driver client, skipping dynamic keywords: {e}")
            return

        # Get the keywords from the client object and its nested objects
        yield from self._get_nested_keywords(client.children)

    def __getattr__(self, name: str) -> Optional[Callable]:
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

        # Try to detect if we're being called by Robot Framework or by a language server
        if not self._is_robot_running():
            logger.info("__getattr__: Called by language server or documentation tool, skipping dynamic keywords")
            return None

        # Get the client, which might be a stub client if not running in Robot Framework
        client = self._get_client()

        # Navigate the object hierarchy to find the attribute
        return self._find_attribute_in_client(client, name)

    def _find_attribute_in_client(self, obj: Any, name: str) -> Optional[Callable]:
        """Find an attribute in the client object by navigating its hierarchy.

        Args:
            obj: The client object to navigate
            name: The attribute name to find

        Returns:
            The callable attribute if found, None otherwise

        Raises:
            Error: If the attribute can't be found and we're running in Robot Framework
        """
        # Split the name into parts to navigate the object hierarchy
        parts = name.split("_")
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
                # If we didn't find any valid attribute, raise an error if running in RF
                # Otherwise return None for language servers/docs tools
                if self._is_robot_running():
                    raise Error(f"Cannot find attribute in path: {name}")
                return None

            # If we've navigated to a callable and there are no more parts, we're done
            if not remaining_parts and callable(obj):
                return obj

        # No matching attribute found
        return None

    def _is_robot_running(self) -> bool:
        """Utility method to check if Robot Framework is actually running.

        This method uses the BuiltIn.robot_running property if available,
        otherwise falls back to the _suite_running flag.

        Returns:
            True if Robot Framework is running tests, False otherwise
        """
        if self._builtin is not None:
            return self._builtin.robot_running
        return False


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
        logger.info("JumpstarterLibraryListener: Test Suite Started")

    def end_suite(self, suite, result) -> None:
        """Called at the end of the test suite.

        This method is automatically called by Robot Framework when the test suite ends.
        It releases the lease if one was acquired.

        Args:
            suite: The test suite object
            result: The test suite result object
        """
        logger.info("JumpstarterLibraryListener: Test Suite Ended")
        if self.library._lease is not None:
            logger.info(
                "JumpstarterLibraryListener: Automatically releasing Jumpstarter lease at the end of the test suite"
            )
            self.library._release_lease()

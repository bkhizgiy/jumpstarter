import asyncio
import socket
from dataclasses import dataclass, field
from enum import IntEnum

from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity import config, engine
from pysnmp.entity.rfc3413 import cmdgen
from pysnmp.proto import rfc1902

from jumpstarter.driver import Driver, export


class PowerState(IntEnum):
    OFF = 0
    ON = 1

class SNMPError(Exception):
    """Base exception for SNMP errors"""
    pass

@dataclass(kw_only=True)
class SNMPServer(Driver):
    """SNMP Power Control Driver"""
    host: str = field()
    user: str = field()
    port: int = field(default=161)
    quiescent_period: int = field(default=5)
    timeout: int = 3
    plug: int = field()
    oid: str = field(default="1.3.6.1.4.1.13742.6.4.1.2.1.2.1")
    auth_protocol: str = field(default=None)  # 'MD5' or 'SHA'
    auth_key: str = field(default=None)
    priv_protocol: str = field(default=None)  # 'DES' or 'AES'
    priv_key: str = field(default=None)

    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()

        try:
            self.ip_address = socket.gethostbyname(self.host)
            self.logger.debug(f"Resolved {self.host} to {self.ip_address}")
        except socket.gaierror as e:
            raise SNMPError(f"Failed to resolve hostname {self.host}: {e}") from e

        self.full_oid = tuple(int(x) for x in self.oid.split('.')) + (self.plug,)

    def _setup_snmp(self):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        snmp_engine = engine.SnmpEngine()

        if self.auth_protocol and self.auth_key:
            if self.priv_protocol and self.priv_key:
                security_level = 'authPriv'
                auth_protocol = getattr(config, f'usmHMAC{self.auth_protocol}AuthProtocol')
                priv_protocol = getattr(config, f'usmPriv{self.priv_protocol}Protocol')

                config.add_v3_user(
                    snmp_engine,
                    self.user,
                    auth_protocol,
                    self.auth_key,
                    priv_protocol,
                    self.priv_key
                )
            else:
                security_level = 'authNoPriv'
                auth_protocol = getattr(config, f'usmHMAC{self.auth_protocol}AuthProtocol')

                config.add_v3_user(
                    snmp_engine,
                    self.user,
                    auth_protocol,
                    self.auth_key
                )
        else:
            security_level = 'noAuthNoPriv'
            config.add_v3_user(
                snmp_engine,
                self.user,
                config.USM_AUTH_NONE,
                None
            )

        config.add_target_parameters(
            snmp_engine,
            "my-creds",
            self.user,
            security_level
        )

        config.add_transport(
            snmp_engine,
            udp.DOMAIN_NAME,
            udp.UdpAsyncioTransport().open_client_mode()
        )

        config.add_target_address(
            snmp_engine,
            "my-target",
            udp.DOMAIN_NAME,
            (self.ip_address, self.port),
            "my-creds"
        )

        return snmp_engine

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_snmp.client.SNMPServerClient"

    def _snmp_set(self, state: PowerState):
        result = {"success": False, "error": None}

        def callback(snmpEngine, sendRequestHandle, errorIndication,
                    errorStatus, errorIndex, varBinds, cbCtx):
            self.logger.debug(f"Callback {errorIndication} {errorStatus} {errorIndex} {varBinds}")
            if errorIndication:
                self.logger.error(f"SNMP error: {errorIndication}")
                result["error"] = f"SNMP error: {errorIndication}"
            elif errorStatus:
                self.logger.error(f"SNMP status: {errorStatus}")
                result["error"] = (
                    f"SNMP error: {errorStatus.prettyPrint()} at "
                    f"{varBinds[int(errorIndex) - 1][0] if errorIndex else '?'}"
                )
            else:
                result["success"] = True
                for oid, val in varBinds:
                    self.logger.debug(f"{oid.prettyPrint()} = {val.prettyPrint()}")
            self.logger.debug(f"SNMP set result: {result}")

        try:
            self.logger.info(f"Sending power {state.name} command to {self.host}")

            snmp_engine = self._setup_snmp()

            cmdgen.SetCommandGenerator().send_varbinds(
                snmp_engine,
                "my-target",
                None,
                "",
                [(self.full_oid, rfc1902.Integer(state.value))],
                callback,
            )

            snmp_engine.open_dispatcher(self.timeout)
            snmp_engine.close_dispatcher()

            if not result["success"]:
                raise SNMPError(result["error"])

            return f"Power {state.name} command sent successfully"

        except Exception as e:
            error_msg = f"SNMP set failed: {str(e)}"
            self.logger.error(error_msg)
            raise SNMPError(error_msg) from e

    @export
    def on(self):
        """Turn power on"""
        return self._snmp_set(PowerState.ON)

    @export
    def off(self):
        """Turn power off"""
        return self._snmp_set(PowerState.OFF)

    def close(self):
        """No cleanup needed since engines are created per operation"""
        if hasattr(super(), "close"):
            super().close()

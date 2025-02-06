# SNMP

**driver**: `jumpstarter_driver_snmp.driver.SNMPServer`

A driver for controlling power via SNMP-enabled PDUs (Power Distribution Units).

## Driver configuration
```yaml
export:
  power:
    type: "jumpstarter_driver_snmp.driver.SNMPServer"
    config:
      host: "pdu.mgmt.com"
      user: "labuser"
      plug: 32
      port: 161
      oid: "1.3.6.1.4.1.13742.6.4.1.2.1.2.1"
      auth_protocol: "NONE"
      auth_key: null
      priv_protocol: "NONE"
      priv_key: null
      timeout: 5.0
```

### Config parameters

| Parameter | Description | Type | Required | Default |
|-----------|-------------|------|----------|---------|
| host | Hostname or IP address of the SNMP-enabled PDU | str | yes | |
| user | SNMP v3 username | str | yes | |
| plug | PDU outlet number to control | int | yes | |
| port | SNMP port number | int | no | 161 |
| oid | Base OID for power control | str | no | "1.3.6.1.4.1.13742.6.4.1.2.1.2.1" |
| auth_protocol | Authentication protocol ("NONE", "MD5", "SHA") | str | no | "NONE" |
| auth_key | Authentication key when auth_protocol is not "NONE" | str | no | null |
| priv_protocol | Privacy protocol ("NONE", "DES", "AES") | str | no | "NONE" |
| priv_key | Privacy key when priv_protocol is not "NONE" | str | no | null |
| timeout | SNMP timeout in seconds | float | no | 5.0 |

## SNMPServerClient API

### Methods

#### on()
Turn power on for the configured outlet.

Returns:
- str: Confirmation message

#### off()
Turn power off for the configured outlet.

Returns:
- str: Confirmation message

#### cycle(quiescent_period: int = 2)
Power cycle the device with a configurable wait period between off and on states.

Parameters:
- quiescent_period: Time to wait in seconds between power off and power on

Returns:
- str: Confirmation message

## Examples

Power cycling a device:
```python
snmp_client.cycle(quiescent_period=3)
```

Basic power control:
```python
snmp_client.off()
snmp_client.on()
```

Using the CLI:
```bash
j power on
j power off
j power cycle --wait 3

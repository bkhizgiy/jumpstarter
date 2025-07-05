# Jumpstarter Architecture Overview

Jumpstarter is an open-source framework for automated hardware and virtual device testing with a focus on democratizing Hardware-in-the-Loop (HiL) testing capabilities.

## Project Purpose

Jumpstarter aims to make hardware testing capabilities accessible to everyone by providing:

- **Unified Testing**: Single tool for local, virtual, and remote hardware testing
- **Hardware Abstraction**: Simplified interfaces for complex hardware through drivers
- **Collaborative Testing**: Global sharing of test hardware resources
- **CI/CD Integration**: Seamless integration with cloud-native developer environments
- **Cross-Platform Support**: Works on Linux and macOS

## Core Architecture Components

### 1. Device Under Test (DUT)

The hardware or virtual device being tested. Can be:

- Physical embedded devices
- Virtual machines (QEMU, etc.)
- Simulated hardware
- IoT devices
- Development boards

### 2. Drivers

Python modules that provide standardized interfaces to device hardware connections:

- **Hardware Abstraction**: Hide device-specific implementation details
- **Consistent APIs**: Uniform interface across different hardware types
- **Modular Design**: Pluggable components for different device types

Example driver types:

- Power control (energenie, yepkit, tasmota)
- Serial communication (pyserial, uboot)
- Network interfaces (shell, http, snmp)
- Storage interfaces (opendal, tftp)
- Hardware debugging (probe-rs, jtag)

### 3. Adapters

Transform driver connections into specialized formats:

- **Protocol Conversion**: Convert from a gRPC stream to a specific protocol such as HTTP
- **Stream Processing**: Handle data transformation and routing
- **Virtual Interfaces**: Create virtual representations of hardware interfaces
- **Integration Helpers**: Bridge gaps between different system components

### 4. Exporters

Manage drivers/adapters and expose them over the network via gRPC:

- **Device Management**: Control multiple drivers for a single DUT
- **Network Exposure**: Make local hardware accessible remotely
- **Configuration**: YAML-based configuration for device setup
- **Resource Isolation**: Ensure exclusive access to hardware resources

### 5. Clients

Libraries and CLI tools for device interaction:

- **Python Libraries**: Programmatic access to device functionality
- **CLI Tools**: Command-line interface (`j` commands)
- **Testing Integration**: Works with pytest, unittest, and other frameworks
- **Interactive Access**: Shell-like interfaces for manual device control

### 6. Service (Kubernetes Controller/Router)

Manages resource allocation and access control in distributed environments:

- **Resource Management**: Coordinate access to shared hardware
- **Authentication**: JWT token-based security model
- **Lease Management**: Exclusive access grants with time limits
- **Multi-tenancy**: Support for multiple users and teams

## Operation Modes

### Local Mode

Direct client-to-exporter communication:

- **Development Focus**: Individual developers with accessible hardware
- **No Infrastructure**: No Kubernetes or external services required
- **Socket Communication**: Local gRPC via Unix sockets
- **Rapid Iteration**: Fast development and testing cycles

### Distributed Mode

Kubernetes-managed resource sharing:

- **Team Collaboration**: Multiple users sharing hardware resources
- **CI/CD Integration**: Automated testing in pipelines
- **Geographic Distribution**: Devices spread across locations
- **Enterprise Security**: JWT authentication and access control

## Communication Architecture

All communication uses gRPC for:

- **Type Safety**: Protocol buffer definitions ensure consistency
- **Performance**: Efficient binary protocol
- **Cross-Language**: Support for multiple programming languages
- **Streaming**: Real-time data streams for device interactions

## Technology Stack

- **Language**: Python 3.11+
- **Packaging**: UV package manager with monorepo structure
- **Communication**: gRPC with Protocol Buffers
- **Container Runtime**: Docker/Podman support
- **Orchestration**: Kubernetes for distributed mode
- **Testing**: pytest integration with custom fixtures
- **Documentation**: Sphinx with MyST markdown

## Key Design Principles

1. **Modularity**: Pluggable drivers and adapters
2. **Consistency**: Uniform APIs across different hardware
3. **Scalability**: From single developer to large teams
4. **Security**: Comprehensive authentication and authorization
5. **Flexibility**: Support for various deployment models
6. **Open Source**: Apache 2.0 licensed with community development

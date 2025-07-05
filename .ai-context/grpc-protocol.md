# gRPC Protocol and Communication

Jumpstarter uses gRPC with Protocol Buffers for all inter-component communication, providing type-safe, efficient, and language-agnostic messaging.

## Protocol Architecture

### Communication Patterns

#### 1. Client ↔ Exporter (Direct)

**Local Mode**: Direct gRPC connection via Unix socket or TCP

```text
Client → gRPC → Local Exporter → Driver → Hardware
```

#### 2. Client ↔ Service ↔ Exporter (Routed)

**Distributed Mode**: Routed through Kubernetes service

```text
Client → gRPC → Router (Request Routing) → gRPC → Exporter → Driver → Hardware
```

#### 3. Exporter ↔ Service (Registration)

**Service Discovery**: Exporters register with the controller

```text
Exporter → gRPC → Controller (Registration, Health, Heartbeat)
```

## Protocol Buffer Definitions

### Core Location

**Generated Protocol Code**: `packages/jumpstarter-protocol/`

The protocol package contains all `.proto` files and generated Python bindings:

```text
jumpstarter_protocol/
├── jumpstarter/
│   ├── v1/
│   │   ├── jumpstarter_pb2.py      # Core service definitions
│   │   ├── router_pb2.py           # Message routing
│   │   └── kubernetes_pb2.py       # Kubernetes integration
│   └── client/
│       └── v1/
│           └── client_pb2.py       # Client-specific protocols
```

### Protocol Generation

#### Build Process

```bash
# Generate from .proto files
buf generate

# Generated files are committed to repository
# Located in packages/jumpstarter-protocol/
```

#### Version Management

- **Backward Compatibility**: Maintained across minor versions
- **Semantic Versioning**: Breaking changes increment major version
- **Field Evolution**: Use of optional fields and deprecation markers

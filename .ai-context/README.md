# AI Context Documentation

This directory contains comprehensive AI context documentation for the Jumpstarter project, designed to help AI assistants understand the project structure, architecture, and development patterns.

## Context Files

### Architecture and Structure

- **[architecture-overview.md](architecture-overview.md)** - High-level system architecture and core components
- **[uv-monorepo-structure.md](uv-monorepo-structure.md)** - UV package manager and monorepo organization
- **[grpc-protocol.md](grpc-protocol.md)** - gRPC communication protocols and patterns
- **[driver-categories.md](driver-categories.md)** - Driver classification and common patterns

### Development Guides

- **[development-workflow.md](development-workflow.md)** - Development processes and project organization
- **[driver-development.md](driver-development.md)** - Driver development patterns and best practices
- **[testing-patterns.md](testing-patterns.md)** - Testing strategies and conventions
- **[documentation-authoring.md](documentation-authoring.md)** - Documentation writing guidelines

### Tools and CLI

- **[cli-tools.md](cli-tools.md)** - Command-line interfaces and usage patterns

## Usage by AI Tools

### Claude Code

The main context entry point is [`../CLAUDE.md`](../CLAUDE.md), which references these files using `@` notation.

### Gemini CLI

The main context entry point is [`../GEMINI.md`](../GEMINI.md), which provides tailored context for Google's Gemini.

### GitHub Copilot / VS Code

Context is provided through [`../.github/copilot-instructions.md`](../.github/copilot-instructions.md) for IDE integration.

### Cursor

Cursor can use any of the context files directly or through the main entry points.

## Structure Philosophy

The AI context system follows a hierarchical approach:

1. **Root-level contexts** - Main entry points for different AI tools
2. **Shared contexts** - Common documentation used by multiple tools
3. **Package-specific contexts** - Detailed context for individual packages
4. **Nested contexts** - Specialized context for complex packages

## Contributing

When adding new context:

1. Follow the existing documentation patterns
2. Update relevant index files (like this README)
3. Reference new files in the appropriate root-level context files
4. Test context effectiveness with actual AI tools

## Context Maintenance

- Keep contexts synchronized with code changes
- Update references when files are moved or renamed
- Validate that contexts remain helpful and accurate
- Remove obsolete or redundant information

# Testing Help Prompt Template

Use this template when asking AI assistants to help with testing in Jumpstarter.

## Context

I need help testing [COMPONENT_TYPE] in the Jumpstarter framework:

- Component: [PACKAGE_NAME]
- Type: [Driver/CLI/Core/Protocol]
- Current issue: [PROBLEM_DESCRIPTION]

## Testing Scope

- [ ] Unit tests for individual methods
- [ ] Integration tests with real hardware
- [ ] Client-server communication tests
- [ ] Configuration validation tests
- [ ] Error handling tests
- [ ] Performance tests

## Current Testing Setup

- Test files: [LIST_EXISTING_TEST_FILES]
- Test coverage: [CURRENT_COVERAGE]
- Mocking strategy: [MOCKING_APPROACH]
- Hardware requirements: [HARDWARE_NEEDED]

## Specific Testing Challenges

[DESCRIBE_SPECIFIC_TESTING_ISSUES]

## Test Environment

- Python version: [VERSION]
- pytest version: [VERSION]
- Hardware available: [YES/NO/MOCKED]
- CI/CD integration: [GITHUB_ACTIONS/OTHER]

## Expected Test Coverage

The tests should cover:

1. [FUNCTIONALITY_1]
2. [FUNCTIONALITY_2]
3. [ERROR_SCENARIOS]
4. [EDGE_CASES]

## Help Needed

- [ ] Test structure design
- [ ] Mock implementation
- [ ] Async test patterns
- [ ] Hardware simulation
- [ ] Performance benchmarks
- [ ] CI/CD integration

---

*Use this template by filling in the bracketed placeholders with your specific testing requirements.*

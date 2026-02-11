# CLAUDE.md

## Architecture

- Follow **Clean Architecture** principles strictly: separate layers for entities, use cases, interface adapters, and frameworks/drivers.
- Dependencies must point inward — outer layers depend on inner layers, never the reverse.
- Each layer must communicate through **well-defined interfaces** (abstractions, not concretions).

## Dependency Injection

- **Dependency Injection is mandatory** for every module. No module should instantiate its own dependencies directly.
- All dependencies must be injected through constructors or dedicated DI containers.
- Prefer interface-based injection to keep modules decoupled and testable.

## Interfaces

- Every service, repository, and external integration must have a clearly defined interface.
- Implementations must be swappable without modifying consuming code.
- Keep interfaces minimal and focused (Interface Segregation Principle).

## AWS Services

- When working with AWS services (SDK, CDK, Lambda, S3, DynamoDB, SQS, etc.), **always use Context7 MCP to fetch up-to-date documentation** before writing or modifying code.
- Do not rely on cached or assumed knowledge for AWS APIs — resolve via Context7 first.

## Terraform

- All infrastructure must be defined as code using **Terraform**.
- When writing or modifying Terraform configurations, **always use Context7 MCP to fetch up-to-date Terraform documentation** (providers, resources, data sources).
- Follow Terraform best practices: use modules, variables, outputs, and remote state.

## General

- Write clean, testable, and maintainable code.
- Prefer composition over inheritance.
- Keep functions and methods small and focused on a single responsibility.

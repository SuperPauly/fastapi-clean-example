# Source Code Directory (`src/`)

This directory contains the core application source code organized according to **Hexagon Architecture** (also known as Ports and Adapters Architecture). The hexagon architecture promotes separation of concerns by organizing code into distinct layers with clear boundaries and dependencies.

## 🏗️ Hexagon Architecture Overview

The hexagon architecture consists of concentric layers where dependencies flow inward:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                INFRASTRUCTURE LAYER                 │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              APPLICATION LAYER              │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │           DOMAIN LAYER              │   │   │   │
│  │  │  │    (Business Logic & Entities)      │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

### Core Layers

| Directory | Layer | Purpose | Dependencies |
|-----------|-------|---------|--------------|
| [`domain/`](./domain/) | **Domain Layer** | Business entities, value objects, domain services | None (pure business logic) |
| [`application/`](./application/) | **Application Layer** | Use cases, application services, ports (interfaces) | Domain layer only |
| [`infrastructure/`](./infrastructure/) | **Infrastructure Layer** | External adapters, databases, web frameworks, task queues | Application & Domain layers |
| [`presentation/`](./presentation/) | **Presentation Layer** | User interfaces, APIs, CLIs, TUIs | All layers |

## 🎯 Key Principles

### 1. **Dependency Inversion**
- Inner layers define interfaces (ports)
- Outer layers implement these interfaces (adapters)
- Dependencies always point inward

### 2. **Separation of Concerns**
- Each layer has a single responsibility
- Business logic is isolated from technical details
- Easy to test and maintain

### 3. **Technology Independence**
- Core business logic doesn't depend on frameworks
- Can swap databases, web frameworks, or UIs without changing business logic
- Facilitates testing with mock implementations

## 🔄 Data Flow

```
User Request → Presentation → Infrastructure → Application → Domain
                     ↓              ↓             ↓          ↓
User Response ← Presentation ← Infrastructure ← Application ← Domain
```

### Example Flow: Creating an Author

1. **Presentation Layer**: FastAPI controller receives HTTP request
2. **Infrastructure Layer**: Validates request, handles authentication
3. **Application Layer**: Executes "Create Author" use case
4. **Domain Layer**: Creates Author entity with business rules
5. **Application Layer**: Calls repository port to save author
6. **Infrastructure Layer**: Repository adapter saves to PostgreSQL
7. **Presentation Layer**: Returns HTTP response

## 🧪 Testing Strategy

Each layer can be tested independently:

- **Domain Layer**: Pure unit tests (no mocks needed)
- **Application Layer**: Unit tests with mocked ports
- **Infrastructure Layer**: Integration tests with real external services
- **Presentation Layer**: End-to-end tests with full stack

## 📋 Usage Guidelines

### ✅ Do's

- Keep domain logic pure (no external dependencies)
- Define clear interfaces in the application layer
- Implement adapters in the infrastructure layer
- Use dependency injection for loose coupling
- Test each layer independently

### ❌ Don'ts

- Don't let domain layer depend on infrastructure
- Don't put business logic in presentation or infrastructure layers
- Don't bypass the application layer from presentation
- Don't create circular dependencies between layers

## 🚀 Getting Started

1. **Start with Domain**: Define your business entities and rules
2. **Define Application**: Create use cases and ports
3. **Implement Infrastructure**: Build adapters for external services
4. **Add Presentation**: Create user interfaces

## 📚 Further Reading

- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Ports and Adapters Pattern](https://herbertograca.com/2017/09/14/ports-adapters-architecture/)


## 1. Core Philosophy

### 1.1 Philosophy

The system must prioritize clarity, maintainability, and long-term coherence over short-term speed. Code should be explicit, predictable, and easy to reason about. All development, including AI-assisted output, must align with a consistent structure and avoid fragmentation.

### 1.2 Rules

1.1.1 Prefer simple and explicit implementations over clever or abstract ones
1.1.2 Optimize for maintainability over speed of delivery
1.1.3 Ensure every piece of logic has a clear and intentional location
1.1.4 Avoid premature abstraction
1.1.5 Review and normalize all AI-generated code before accepting it

---

## 2. Project Structure

### 2.1 Philosophy

The project structure should enable separation of concerns and allow major parts of the system (such as frontend or infrastructure) to be replaced with minimal disruption.

### 2.2 Rules

2.1.1 Use a single global templates directory at the project root
2.1.2 Use a single global static directory at the project root
2.1.3 Do not distribute templates or static files across apps
2.1.4 Organize settings into a dedicated settings directory with environment separation
2.1.5 Store user-uploaded media externally and never in the codebase

---

## 3. Application Design

### 3.1 Philosophy

Applications should be modular and focused on domain responsibilities. Shared logic should be centralized only when reuse is proven, and always structured to avoid becoming monolithic.

### 3.2 Rules

3.1.1 Keep apps focused on their domain responsibilities
3.1.2 Centralize shared logic only after reuse is observed
3.1.3 When centralizing logic, organize by domain or concern, not by convenience
3.1.4 Avoid creating large, unstructured shared modules
3.1.5 Ensure all shared logic remains clearly scoped and understandable

---

## 4. Code Organization

### 4.1 Philosophy

Every piece of code must have a clear and predictable location. Code should be organized by responsibility, not by where it is first needed.

### 4.2 Rules

4.1.1 Place reusable, generic logic in a shared utilities module
4.1.2 Place business logic involving models in a structured service layer
4.1.3 Place view-related behavior in mixins where appropriate
4.1.4 Keep app-specific logic within the app unless reuse justifies extraction
4.1.5 Avoid duplication by enforcing a single source of truth for each piece of logic

---

## 5. Duplication and Reuse

### 5.1 Philosophy

Duplication is the primary source of long-term complexity. All logic must have a single authoritative implementation.

### 5.2 Rules

5.1.1 Before implementing new logic, check if it already exists
5.1.2 Reuse existing implementations whenever possible
5.1.3 If similar logic exists in multiple places, refactor into a shared implementation
5.1.4 Do not create parallel implementations of the same concept
5.1.5 Ensure each piece of business logic has one authoritative source

---

## 6. Refactoring

### 6.1 Philosophy

Refactoring is a continuous process and must occur before complexity accumulates. Code should evolve toward clarity and structure.

### 6.2 Rules

6.1.1 Refactor when duplication is identified
6.1.2 Refactor when a file becomes too large or difficult to navigate
6.1.3 Use a threshold of approximately 2000 lines to trigger review
6.1.4 Split code by concern, not arbitrarily
6.1.5 Prefer improving existing code over adding new parallel structures

---

## 7. Models and Business Logic

### 7.1 Philosophy

Models should encapsulate business rules and core logic related to the data they represent.

### 7.2 Rules

7.1.1 Place calculations and derived logic within models where appropriate
7.1.2 Use model methods for state changes and business workflows
7.1.3 Define related_name explicitly for all relationships
7.1.4 Avoid placing business logic in views
7.1.5 Avoid excessive reliance on signals; prefer explicit logic

---

## 8. Views and Application Flow

### 8.1 Philosophy

Views should remain thin and focused on handling requests and responses. Business logic should be delegated elsewhere.

### 8.2 Rules

8.1.1 Keep views limited to request handling and response construction
8.1.2 Do not implement business logic directly in views
8.1.3 Use class-based views where appropriate for structure and reuse
8.1.4 Monitor view file size and refactor when approaching defined limits
8.1.5 Delegate complex workflows to services or models

---

## 9. Query Optimization

### 9.1 Philosophy

Database efficiency is a core requirement. Poor query design leads to performance issues and must be avoided from the outset.

### 9.2 Rules

9.1.1 Always consider query efficiency when retrieving data
9.1.2 Use select_related for foreign key relationships
9.1.3 Use prefetch_related for reverse and many-to-many relationships
9.1.4 Avoid N+1 query patterns
9.1.5 Paginate large datasets

---

## 10. Templates and Frontend Structure

### 10.1 Philosophy

Templates should be structured, reusable, and focused solely on presentation. The frontend must be replaceable without affecting backend logic.

### 10.2 Rules

10.1.1 Keep templates free of business logic
10.1.2 Use includes to create reusable components
10.1.3 Avoid large, monolithic templates
10.1.4 Organize templates into layouts, components, and pages
10.1.5 Do not duplicate UI structures across templates

---

## 11. Forms and Validation

### 11.1 Philosophy

Validation should be handled in a structured and consistent manner, relying on framework tools wherever possible.

### 11.2 Rules

11.1.1 Use framework-provided form handling for validation
11.1.2 Avoid manual parsing of request data
11.1.3 Validate data at multiple levels where appropriate
11.1.4 Keep validation logic consistent and centralized

---

## 12. File and Media Handling

### 12.1 Philosophy

File handling must be secure, structured, and independent of the application codebase.

### 12.2 Rules

12.1.1 Store media externally
12.1.2 Validate file type and size on upload
12.1.3 Use structured and predictable file paths
12.1.4 Avoid direct exposure of sensitive media

---

## 13. Naming and Conventions

### 13.1 Philosophy

Consistent naming improves readability, reduces confusion, and enforces structure across the system.

### 13.2 Rules

13.1.1 Use clear and descriptive names for all code elements
13.1.2 Use consistent naming patterns across apps and modules
13.1.3 Ensure names reflect purpose and responsibility

---

## 14. Environment and Configuration

### 14.1 Philosophy

Configuration must be environment-specific, secure, and isolated from code.

### 14.2 Rules

14.1.1 Use environment variables for all sensitive configuration
14.1.2 Separate development and production settings
14.1.3 Do not hardcode secrets or environment-specific values

---

## 15. AI-Assisted Development

### 15.1 Philosophy

AI is a tool for acceleration, not decision-making. All structure, organization, and long-term coherence must be enforced explicitly.

### 15.2 Rules

15.1.1 Do not accept AI-generated code without review
15.1.2 Ensure all generated code follows project structure and rules
15.1.3 Prefer incremental development over large code generation
15.1.4 Refactor AI-generated code to align with system design
15.1.5 Enforce duplication prevention and single source of truth at all times

---

## 16. Final Principle

### 16.1 Philosophy

A well-structured system is one where every piece of logic has a clear purpose, a clear location, and a single authoritative implementation.

### 16.2 Rules

16.1.1 If the location of code is unclear, reassess the structure before proceeding
16.1.2 If multiple implementations exist, consolidate them
16.1.3 If complexity increases, refactor early
16.1.4 Maintain consistency across the entire codebase at all times

---

This version is intentionally minimal in tone but strong in enforcement. It should work well both as a personal reference and as a control layer for AI-assisted development.

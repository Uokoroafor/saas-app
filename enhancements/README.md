# SaaS App Project

A subscription-based SaaS application built with Django, HTML, CSS, and JavaScript. This project is a full-stack application designed to demonstrate robust backend development, front-end integration, and deployment practices.

---

##  Features

- User authentication and subscription management
- Dynamic front-end with HTML, CSS, and JavaScript
- Fully functional backend powered by Django
- Deployment-ready with CI/CD

---

## To-Do List

### 1. **Workflow Changes**
- [X] Refactor GitHub Actions YAML files for efficiency
- [X] Add reusable workflows for CI/CD
- [X] Integrate notifications for build/test statuses (e.g., Slack or email)

### 2. **Dockerisation**
- [X] Create a `Dockerfile` for the application
- [X] Set up `docker-compose.yml` for full-stack containerisation 
- [ ] Optimise Docker image size using multi-stage builds
- [X] Document setup instructions for running the Dockerised version locally

### 3. **Linting and Code Style**
- [X] Add type hints to all functions and methods
- [X] Write detailed docstrings following a consistent style guide
- [X] Set up `mypy` and `ruff` for linting and type-checking
- [X] Automate linting and type-checking using pre-commit hooks

### 4. **Code Refactoring**
- [X] Identify and reduce duplication across the codebase
- [X] Break down large views or methods into smaller components


### 5. **Dependency Management**
- [X] Transition from `requirements.txt` to Poetry (`pyproject.toml`)
- [X] Document how to use Poetry for dependency management
- [X] Set up a fallback `requirements.txt` export for compatibility

### 6. **Front-End Redesign**
- [X] Redesign the front-end for improved usability and responsiveness
- [X] Add a 'Contact Us' page
- [X] Build other main page components

### 7. **Implement Back-End Logger**
- [X] Remove unnecessary instances of the print function
- [X] Implement a Logger
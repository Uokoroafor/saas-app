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
<!-- - [ ] Integrate notifications for build/test statuses (e.g., Slack or email) -->

### 2. **Testing**
- [ ] Build a testing suite using `pytest` 
  - [ ] Unit tests for critical functions
  - [ ] Integration tests for end-to-end workflows
- [ ] Measure test coverage with `coverage.py`
- [ ] Add automated testing to CI/CD pipeline

### 3. **Dockerisation**
- [X] Create a `Dockerfile` for the application
- [ ] Set up `docker-compose.yml` for full-stack containerisation (e.g., Django + PostgreSQL)
- [ ] Optimise Docker image size using multi-stage builds
- [ ] Document setup instructions for running the Dockerised version locally

### 4. **Linting and Code Style**
- [ ] Add type hints to all functions and methods
- [ ] Write detailed docstrings following a consistent style guide
- [X] Set up `mypy`, `ruff` and `black` for linting and type-checking
- [X] Automate linting and type-checking using pre-commit hooks

### 5. **Code Refactoring**
- [ ] Identify and reduce duplication across the codebase
- [ ] Break down large views or methods into smaller components
- [ ] Optimise database queries with Django ORM tools
- [ ] Extract business logic into service classes or utilities

### 6. **Dependency Management**
- [ ] Transition from `requirements.txt` to Poetry (`pyproject.toml`)
- [ ] Document how to use Poetry for dependency management
- [ ] Set up a fallback `requirements.txt` export for compatibility

### 7. **Front-End Redesign**
- [ ] Redesign the front-end for improved usability and responsiveness

### 8. **Implement Back-End Logger**
- [ ] Remove instances of the print function
- [ ] Implement a Logger

---

<!-- 
## Contributing

Contributions are welcome! If you'd like to suggest improvements or report issues, feel free to open a pull request or issue.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details. -->
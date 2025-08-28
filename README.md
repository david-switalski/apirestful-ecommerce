# API RESTful para E-Commerce

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/david-switalski/apirestful-ecommerce/main.yml) ![Codecov](https://img.shields.io/codecov/c/github/david-switalski/apirestful-ecommerce) ![GitHub License](https://img.shields.io/github/license/david-switalski/apirestful-ecommerce)

![Python](https://img.shields.io/badge/Python-3.12-blue.svg) ![FastAPI](https://img.shields.io/badge/Framework-FastAPI-green.svg) ![Database](https://img.shields.io/badge/Database-PostgreSQL-blue.svg) ![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg) ![Tests](https://img.shields.io/badge/Tests-Pytest-brightgreen.svg)


![API General Flow](assets/api-flow.gif)

---

## Overview
This project is a robust and scalable RESTful API designed for an E-Commerce platform. Built with **FastAPI** and **SQLAlchemy** in a fully asynchronous environment, it provides a solid foundation for managing products, users, and authentication. The API is fully containerized with **Docker**, ensuring a simple and consistent deployment across any environment.

---

## Features

*   **Asynchronous Architecture:** High performance and concurrency thanks to FastAPI and `asyncpg`.
*   **Secure JWT Authentication:** Implements `access tokens` and `refresh tokens` for secure and flexible session management.
*   **Role-Based Authorization:** Protected endpoints that distinguish between users (`user`) and administrators (`admin`), ensuring that only authorized personnel can perform critical operations.
*   **Full Product Management (CRUD):** Endpoints to create, read, update, and delete products, with restricted access for administrators.
*   **Full User Management (CRUD):** Allows new user registration and complete management by administrators.
*   **Database Migrations:** Integration with **Alembic** to version and manage the database schema safely.
*   **Fully Containerized:** A ready-to-use `docker-compose.yml` configuration to launch the application and database with a single command.
*   **Comprehensive Test Suite:** Unit and integration tests with **Pytest** and **HTTPX** to ensure code reliability.
*   **Automated Code Quality:** **pre-commit** configuration to run `detect-secrets` and other linters before each commit.

---

## Technologies Used

*   **Backend:** FastAPI, Uvicorn
*   **Database:** PostgreSQL, SQLAlchemy (with `asyncio` support)
*   **Migrations:** Alembic
*   **Authentication:** PyJWT, passlib, bcrypt
*   **Data Validation:** Pydantic
*   **Testing:** Pytest, pytest-asyncio, HTTPX
*   **Containerization:** Docker, Docker Compose
*   **Code Quality:** pre-commit, detect-secrets

---

## Project Structure

The project follows a modular and organized structure to enhance maintainability and scalability.

```bash
apirestful-ecommerce/
├── alembic/                   # Alembic scripts and configuration for migrations
├── assets/                    # Static assets (e.g., images, fonts, gifs)
├── scripts/                   # Utility scripts (e.g., create superuser)
├── src/                       # Main source code directory
│   ├── auth/                  # Authentication logic and security dependencies
│   ├── core/                  # Core configuration and custom exceptions
│   ├── data_base/             # DB session setup and base classes
│   ├── models/                # SQLAlchemy models (DB tables)
│   ├── routers/               # API endpoints (controllers)
│   ├── schemas/               # Pydantic schemas (data validation)
│   ├── services/              # Business logic
│   └── main.py                # FastAPI application entry point
├── tests/                     # Automated tests
├── .dockerignore              # Files to be ignored by Docker
├── .env.example               # Template for environment variables
├── .gitignore                 # Files to be ignored by Git
├── .pre-commit-config.yaml    # Configuration for pre-commit hooks
├── alembic.ini                # Alembic configuration file
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Application image definition
├── LICENSE                
├── pytest.ini                 # Pytest configuration file
├── README.md                  
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Development dependencies
```

---

## Prerequisites

Before you begin, please ensure you have the following tools installed and configured on your local machine.

*   **Git:** You'll need Git to clone the repository. You can download it from [git-scm.com](https://git-scm.com/downloads).
*   **Python 3.12+:** The application is built with Python 3.12. You can download it from the [official Python website](https://www.python.org/downloads/).
*   **Docker & Docker Compose:** The project is fully containerized. You will need Docker to build and run the services. Docker Desktop for Windows and Mac includes Docker Compose.
    *   [Install Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended for Mac/Windows).
    *   [Install Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) for Linux.

---
   
## Installation and Setup

Follow these steps to set up and run the project in your local environment.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/david-switalski/apirestful-ecommerce.git
    cd apirestful-ecommerce
    ```

2.  **Create and activate a virtual environment (recommended):**
    *   **Create the environment:**
        ```bash
        python -m venv venv
        ```
    *   **Activate the environment:**
        *   On Windows:
            ```bash
            .\venv\Scripts\activate
            ```
        *   On macOS/Linux:
            ```bash
            source venv/bin/activate
            ```

3.  **Install the dependencies:**
    With your virtual environment activated, install all necessary dependencies (including development ones).
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file from the provided example.
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and fill in all the variables. For `SECRET_KEY`, you can generate a secure key with:
    ```bash
    python -c "import secrets; print(secrets.token_hex(32))"
    ```

5.  **Start the services with Docker Compose (Recommended Method):**
    This command will build the image, create the containers, and apply the database migrations.
    ```bash
    docker-compose up --build
    ```

The API will be available at `http://localhost:8000`.

---

## How to Use the API

The easiest way to explore and test the API is through the interactive documentation.
### Interactive Documentation

FastAPI automatically generates an interactive documentation. You can access it at:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---
### Authentication Flow

While you can authenticate directly within the Swagger UI, the following GIF uses **Postman** to demonstrate the raw HTTP flow for obtaining and using a JWT token. This is how a real-world application would interact with the API.

![API Authentication Flow with Postman](assets/api-auth-flow2-postman.gif)

**The flow consists of these steps:**

- Sending a **`POST`** request with user credentials to the `/users/token` endpoint.
- Receiving an **`access_token`** in the response.
- Using this token in the **`Authorization: Bearer <token>`** header for all subsequent requests to protected endpoints.

### Creating a Superuser
To access the admin endpoints, you must first create a superuser. With the containers running, open a new terminal and run:

```bash
docker-compose exec web python -m scripts.create_super_user
```
This will create a user with the following default credentials:
*   **Username:** `SuperUser`
*   **Password:** `Test12345$`

### Database Management
The project uses Alembic for migrations. To create a new migration after modifying the models in `src/models/`:
```bash
docker-compose exec web alembic revision --autogenerate -m "Migration message"
```
To apply the migrations:
```bash
docker-compose exec web alembic upgrade head
```

---

## Running Tests

The test suite is designed to run locally against a temporary test database, ensuring your development data is not affected.

**Prerequisite:** The Docker database container must be running.

1.  **Start the database service only:**
    If you don't have the full application running, you can start just the database container in the background:
    ```bash
    docker-compose up -d db
    ```
    This ensures that `pytest` has a PostgreSQL server to connect to at `localhost:5432`.

2.  **Run Pytest:**
    Make sure your virtual environment is activated and the dependencies are installed. Then, from the project root, run:
    ```bash
    pytest
    ```
    `pytest` will connect to the running database, create a temporary `test_...` database, run all tests, and delete it upon completion.

---

## Contact

**David Switalski**
*(Informático y Desarrollador en Formación)*

* **LinkedIn:** [David Switalski](https://www.linkedin.com/in/david-switalski-50b11133a/)
* **GitHub:** [David Switalski](https://github.com/david-switalski)
* **Email:** davidspuni@gmail.com

---

## Contribution

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss potential changes or additions.
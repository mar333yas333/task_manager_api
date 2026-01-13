Project Title
	Task Management REST API (Django)

Short Description
	A RESTful API built with Django and Django REST Framework that allows users to register, authenticate, and manage tasks with CRUD operations.

Tech Stack
    - **Backend Framework:** Django 4.2.11
    - **API Framework:** Django REST Framework 3.16.1
    - **Database:** MySQL (with mysqlclient 2.2.7)
    - **Authentication:** Token-based authentication (DRF TokenAuthentication)
    - **CORS Handling:** django-cors-headers 4.9.0
    - **Project Utilities:** django-extensions 4.1
    - **Frontend (optional pages):** Django templates
    - **Development Environment:** Python 3.12, Virtualenv


Features
	- User registration and login
	- Token-based authentication (DRF TokenAuthentication)
	- Create, read, update, and delete tasks
	- User-specific task ownership

Project Structure
	task_management_api/
	├── taskapi/                # Core API configuration and routing
	├── tasks/                  # Tasks application (models, views, serializers)
	├── templates/              # HTML templates 
	├── manage.py               # Django management entry point
	├── requirements.txt        # Project dependencies
	└── README.md

	venv/ is excluded from submission

Installation & Setup
    1. Clone the repository
        git clone https://github.com/yourusername/ment_api.git
        cd ment_api

    2. Create and activate a Python virtual environment
        python -m venv venv
        source venv/bin/activate        # Linux / macOS
        venv\Scripts\activate           # Windows

    3. Install project dependencies
        pip install -r requirements.txt

    4. Configure the database
        - Ensure MySQL is installed and running
        - Create a database named `task_management_db`
        - Update database credentials in `taskapi/settings.py` or use environment variables:
            ```python
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': 'task_management_db',
                    'USER': 'your_db_user',
                    'PASSWORD': 'your_db_password',
                    'HOST': 'localhost',
                    'PORT': '3306',
                }
            }
            ```

    5. Apply migrations
        python manage.py migrate

    6. Create a superuser (optional, for admin access)
        python manage.py createsuperuser

    7. Run the development server
        python manage.py runserver

    8. Access the API
        - Visit http://127.0.0.1:8000/ in your browser
        - Use API endpoints as defined in your project


API Endpoints
    ### TaskViewSet (CRUD)

    1. List all tasks
        - URL: /api/tasks/
        - Method: GET
        - Description: Retrieves all tasks

    2. Create a task
        - URL: /api/tasks/
        - Method: POST
        - Description: Creates a new task
        - Request body:
            {
                "title": "Task title",
                "completed": false
            }

    3. Retrieve a task
        - URL: /api/tasks/<id>/
        - Method: GET
        - Description: Retrieves a single task by ID

    4. Update a task
        - URL: /api/tasks/<id>/
        - Method: PUT / PATCH
        - Description: Updates an existing task

    5. Delete a task
        - URL: /api/tasks/<id>/
        - Method: DELETE
        - Description: Deletes a task by ID

    ### User Authentication

    6. Register a new user
        - URL: /api/register/
        - Method: POST
        - Description: Creates a new user account
        - Request body:
            {
                "username": "user",
                "password": "pass"
            }

    7. Login
        - URL: /api/login/
        - Method: POST
        - Description: Logs in a user and returns token
        - Request body:
            {
                "username": "user",
                "password": "pass"
            }

    8. Logout
        - URL: /api/logout/
        - Method: POST
        - Description: Logs out the authenticated user

    9. User profile
        - URL: /api/users/profile/
        - Method: GET / PUT
        - Description: View or update user profile

    10. Dashboard
        - URL: /api/dashboard/
        - Method: GET
        - Description: Retrieve dashboard data

    11. Health check
        - URL: /api/health/
        - Method: GET
        - Description: Returns server health status

Authentication Method
    1. Authentication Type
        - Token-based authentication using Django REST Framework
        - Default authentication classes:
            - TokenAuthentication
            - SessionAuthentication

    2. How to authenticate
        - After registering and logging in, the API returns a token for the user
        - Include this token in the `Authorization` header for all protected endpoints
            ```
            Authorization: Token <your_token_here>
            ```

    3. Endpoints requiring authentication
        - /api/logout/            → POST
        - /api/users/profile/     → GET / PUT
        - /api/dashboard/         → GET
        - /api/tasks/             → GET / POST / PUT / PATCH / DELETE
        - Any other API endpoint that uses `IsAuthenticated` permission

    4. Notes
        - Registration and login endpoints (`/api/register/`, `/api/login/`) do not require authentication
        - Ensure the token is included in all subsequent requests to access protected resources
        - Tokens can be managed using Django admin or via DRF endpoints

	
Author
	Author: Marwan Ahmed  
	ALX Back-End Program


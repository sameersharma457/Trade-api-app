# Trade API App

A RESTful API for managing trades, built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- User registration and authentication (JWT)
- CRUD operations for trades
- Portfolio management
- Secure password hashing
- Environment-based configuration

## Requirements

- Python 3.8+
- PostgreSQL
- [pipenv](https://pipenv.pypa.io/en/latest/) or `pip`

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Ns15022001/Trade-api-app.git
cd Trade-api-app
2.Create and Activate a Virtual Environment
Using venv:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Or using pipenv:
pipenv shell
pipenv shell
3. Install Dependencies
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the root directory and add the following (edit as needed):
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
7. Start the Application
uvicorn main:app --reload
The API will be available at http://localhost:8000.

8. API Documentation
Visit http://localhost:8000/docs for interactive Swagger UI.

Project Structure


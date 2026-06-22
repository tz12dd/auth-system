# Secure Authentication System

A complete username/password authentication system built with Python/Flask, featuring JWT tokens, secure password hashing, and best practices for security.

## Features

- ✅ Secure password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ User registration and login endpoints
- ✅ Protected routes with authentication middleware
- ✅ Input validation and sanitization
- ✅ Rate limiting on login attempts
- ✅ CORS configuration
- ✅ Environment-based configuration
- ✅ SQLite database
- ✅ HTML/CSS/JavaScript frontend

## Installation

### Prerequisites
- Python 3.8+
- pip
- Node.js (optional, for frontend build tools)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/tz12dd/auth-system.git
cd auth-system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

5. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

6. Run the application:
```bash
python app.py
```

The backend will start on `http://localhost:5000`

## API Endpoints

### Authentication

#### Register a new user
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

Response (201):
```json
{
  "message": "User registered successfully",
  "user_id": 1
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

Response (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Protected Routes

#### Get current user
```http
GET /api/user/profile
Authorization: Bearer {access_token}
```

Response (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-06-22T10:30:00"
}
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer {access_token}
```

## Frontend Usage

1. Open `index.html` in your browser or serve it with a simple HTTP server:
```bash
python -m http.server 8000
```

2. Navigate to `http://localhost:8000`

3. Use the login/signup forms to test the authentication flow

## Security Features

### Password Security
- Passwords are hashed using bcrypt with 12 salt rounds
- Never stored in plain text
- Minimum 8 characters required

### Token Security
- JWT tokens with 1-hour expiration
- Tokens signed with SECRET_KEY
- Authorization header required for protected routes

### Input Validation
- Email format validation
- Password strength requirements
- SQL injection prevention via SQLAlchemy ORM
- XSS protection with Content-Security-Policy headers

### Rate Limiting
- Login attempts limited to 5 per minute per IP
- Registration limited to 3 per minute per IP

### CORS Configuration
- Configured to allow localhost origins
- Update for production use

## Environment Variables

Create a `.env` file with:
```
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=your-very-secure-random-key-here
JWT_SECRET=your-jwt-secret-key-here
DATABASE_URL=sqlite:///auth.db
CORS_ORIGINS=http://localhost:8000,http://localhost:3000
```

## Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Generate strong random `SECRET_KEY` and `JWT_SECRET`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS for your domain
- [ ] Implement rate limiting at reverse proxy level
- [ ] Set up proper logging and monitoring
- [ ] Use environment variables for sensitive data
- [ ] Implement password reset flow
- [ ] Add email verification
- [ ] Consider 2FA implementation

## Common Issues

### "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "database is locked"
Ensure only one instance of the app is running. SQLite has limitations with concurrent writes.

### CORS errors
Update `CORS_ORIGINS` in `.env` to match your frontend URL.

## Next Steps

1. Add password reset functionality
2. Implement email verification
3. Add refresh token rotation
4. Implement 2FA/MFA
5. Add user profile management
6. Set up comprehensive logging
7. Add API documentation (Swagger)

## Security References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## License

MIT

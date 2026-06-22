import os
from datetime import timedelta
from functools import wraps
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import bcrypt
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JSON_SORT_KEYS'] = False

# Security Headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:8000').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Hash and set the password"""
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    
    def verify_password(self, password):
        """Verify the provided password against the hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @staticmethod
    def _validate_password_strength(password):
        """Validate password meets minimum security requirements"""
        if len(password) < 8:
            return False
        # Must contain uppercase, lowercase, number, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        return has_upper and has_lower and has_digit and has_special
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

# Utility Functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_error_response(message, status_code):
    """Create a standardized error response"""
    return jsonify({'error': message}), status_code

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return create_error_response('No data provided', 400)
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not email:
            return create_error_response('Email is required', 400)
        
        if not password:
            return create_error_response('Password is required', 400)
        
        if not validate_email(email):
            return create_error_response('Invalid email format', 400)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return create_error_response('Email already registered', 409)
        
        # Validate password strength
        try:
            user = User(email=email)
            user.set_password(password)
        except ValueError as e:
            return create_error_response(str(e), 400)
        
        # Create user
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Registration failed: {str(e)}', 500)

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login with email and password"""
    try:
        data = request.get_json()
        
        if not data:
            return create_error_response('No data provided', 400)
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return create_error_response('Email and password are required', 400)
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.verify_password(password):
            return create_error_response('Invalid email or password', 401)
        
        if not user.is_active:
            return create_error_response('User account is inactive', 403)
        
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }), 200
    
    except Exception as e:
        return create_error_response(f'Login failed: {str(e)}', 500)

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile (protected route)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return create_error_response('User not found', 404)
        
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        return create_error_response(f'Failed to fetch profile: {str(e)}', 500)

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (token-based)"""
    # With JWT, logout is typically handled client-side by deleting the token
    # This endpoint can be used for logging, blacklisting, etc.
    return jsonify({'message': 'Logged out successfully'}), 200

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return create_error_response('Resource not found', 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return create_error_response('Method not allowed', 405)

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return create_error_response('Internal server error', 500)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('DEBUG', False), host='0.0.0.0', port=5000)

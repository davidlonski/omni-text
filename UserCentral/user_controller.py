from User import User
import hashlib
import json
import os
from typing import List, Optional

# Global user list
userlist: List[User] = []

# Role permissions mapping
ROLE_PERMISSIONS = {
    'student': {
        'can_upload_files': True,
        'can_describe_images': True,
        'can_take_quiz': True,
        'can_view_own_data': True,
        'can_manage_users': False,
        'can_view_all_data': False,
        'can_configure_app': False
    },
    'teacher': {
        'can_upload_files': True,
        'can_describe_images': True,
        'can_take_quiz': True,
        'can_view_own_data': True,
        'can_manage_users': True,
        'can_view_all_data': True,
        'can_configure_app': True
    },
    'admin': {
        'can_upload_files': True,
        'can_describe_images': True,
        'can_take_quiz': True,
        'can_view_own_data': True,
        'can_manage_users': True,
        'can_view_all_data': True,
        'can_configure_app': True
    }
}

def initialize_users():
    """Initialize default users if no users exist."""
    global userlist
    
    # Load existing users from file if available
    if os.path.exists('users.json'):
        load_users_from_file()
    else:
        # Create default users
        userlist = []
        userlist.append(User(
            name="Admin User", 
            age=30, 
            email="admin@gmail.com", 
            password=__hash_password("admin"), 
            role="admin"
        ))
        userlist.append(User(
            name="Student User", 
            age=20, 
            email="student@gmail.com", 
            password=__hash_password("student"), 
            role="student"
        ))
        userlist.append(User(
            name="Teacher User", 
            age=35, 
            email="teacher@gmail.com", 
            password=__hash_password("teacher"), 
            role="teacher"
        ))
        save_users_to_file()

def create_user(user: User) -> bool:
    """Create a new user. Returns True if successful, False if email already exists."""
    global userlist
    
    # Check if email already exists
    if get_user_by_email(user.email):
        return False
    
    userlist.append(user)
    save_users_to_file()
    return True

def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    for user in userlist:
        if user.id == user_id:
            return user
    return None

def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email."""
    for user in userlist:
        if user.email == email:
            return user
    return None

def update_user(user_id: str, updated_user: User) -> bool:
    """Update user by ID. Returns True if successful, False if user not found."""
    global userlist
    
    for i, user in enumerate(userlist):
        if user.id == user_id:
            userlist[i] = updated_user
            save_users_to_file()
            return True
    return False

def delete_user(user_id: str) -> bool:
    """Delete user by ID. Returns True if successful, False if user not found."""
    global userlist
    
    for user in userlist:
        if user.id == user_id:
            userlist.remove(user)
            save_users_to_file()
            return True
    return False

def validate_user(email: str, password: str) -> Optional[User]:
    """Validate user credentials. Returns User object if valid, None otherwise."""
    user = get_user_by_email(email)
    if user and __verify_password(password, user.password):
        return user
    return None

def get_all_users() -> List[User]:
    """Get all users."""
    return userlist.copy()

def get_users_by_role(role: str) -> List[User]:
    """Get all users with a specific role."""
    return [user for user in userlist if user.role == role]

def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    if not user or user.role not in ROLE_PERMISSIONS:
        return False
    return ROLE_PERMISSIONS[user.role].get(permission, False)

def get_user_permissions(user: User) -> dict:
    """Get all permissions for a user."""
    if not user or user.role not in ROLE_PERMISSIONS:
        return {}
    return ROLE_PERMISSIONS[user.role].copy()

def save_users_to_file():
    """Save users to JSON file."""
    try:
        users_data = [user.dict() for user in userlist]
        with open('users.json', 'w') as f:
            json.dump(users_data, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def load_users_from_file():
    """Load users from JSON file."""
    global userlist
    try:
        with open('users.json', 'r') as f:
            users_data = json.load(f)
            userlist = [User(**user_data) for user_data in users_data]
    except Exception as e:
        print(f"Error loading users: {e}")
        userlist = []

def __hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def __verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password

# Initialize users when module is imported
initialize_users()

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username.
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Authenticate user by email and password.

        Args:
            request: Django request object
            email: User email (case-insensitive)
            password: User password

        Returns:
            User object if authentication successful, None otherwise
        """
        if email is None:
            email = kwargs.get('username')
        if email is None:
            return None
        try:
            # Case-insensitive email lookup
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        
        # Check password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: User primary key
            
        Returns:
            User object if exists, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

from typing import Dict, Optional
import structlog
from src.backend.abstraction import AuthAbstraction


class AuthService:
    def __init__(self, auth_abstraction: AuthAbstraction):
        self.auth_abstraction = auth_abstraction
        self.logger = structlog.get_logger(__name__)

    def login_with_email(self, email: str) -> Dict:
        """
        Login a user with their email address

        Args:
            email: The email address to check

        Returns:
            Dictionary with user info and auth token
        """
        self.logger.info(
            "Login attempt",
            email=email
        )

        try:
            user_data = self.auth_abstraction.login_with_email(email)
            return user_data
        except ValueError as e:
            self.logger.error(
                "Login failed",
                email=email,
                error=str(e)
            )
            raise

    def logout(self, auth_token: str) -> bool:
        """
        Logout a user

        Args:
            auth_token: The authentication token to invalidate

        Returns:
            True if successful, False if token wasn't found
        """
        self.logger.info(
            "Logout attempt",
            auth_token=auth_token
        )

        result = self.auth_abstraction.logout(auth_token)

        if not result:
            self.logger.warning(
                "Logout failed - token not found",
                auth_token=auth_token
            )

        return result

    def verify_token(self, auth_token: str) -> Optional[Dict]:
        """
        Verify if an auth token is valid

        Args:
            auth_token: The authentication token to check

        Returns:
            User data dictionary if valid, None otherwise
        """
        user_data = self.auth_abstraction.verify_token(auth_token)

        if not user_data:
            self.logger.warning(
                "Token verification failed",
                auth_token=auth_token
            )

        return user_data

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user info by email

        Args:
            email: The email to look up

        Returns:
            User data dictionary if found, None otherwise
        """
        self.logger.info(
            "Looking up user by email",
            email=email
        )

        return self.auth_abstraction.get_user_by_email(email)
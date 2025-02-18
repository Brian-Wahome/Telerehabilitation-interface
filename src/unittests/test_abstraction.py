import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from src.backend.abstraction import UserAbstraction


class TestUserAbstraction:
    @pytest.fixture
    def db_session(self):
        """Create a mock db session"""
        return Mock(spec=Session)

    @pytest.fixture
    def user_abstraction(self, db_session):
        """Create UserAbstraction instance with mock session"""
        abstraction = UserAbstraction(db_session)
        return abstraction

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "patient"
        }

    @patch('src.backend.abstraction.User')
    def test_create_user_success(self, mock_user, user_abstraction, sample_user_data):
        """Test successful user creation"""
        created_user = Mock()
        # Mock the User orm initialization
        mock_user.return_value = created_user
        # Call the function
        user_abstraction.create_user(sample_user_data)

        # Assert
        mock_user.assert_called_once_with(**sample_user_data)
        user_abstraction.db.add.assert_called_once_with(created_user)


    def test_create_user_db_error(self, user_abstraction, sample_user_data):
        """Test database error during user creation"""
        # Arrange
        user_abstraction.db.add.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            user_abstraction.create_user(sample_user_data)
        assert str(exc_info.value) == "Database error"
        assert user_abstraction.db.rollback.called  # Confirms db is rolled back on failed transaction

    def test_create_user_transaction_management(self, user_abstraction, sample_user_data):
        """Test transaction management during user creation"""
        user_abstraction.create_user(sample_user_data)

        # Verify transaction was committed
        assert user_abstraction.db.commit.called
        # Verify rollback wasn't called (no errors)
        assert not user_abstraction.db.rollback.called

    def test_create_user_rollback_on_error(self, user_abstraction, sample_user_data):
        """Test transaction rollback on error"""
        # Arrange
        user_abstraction.db.commit.side_effect = Exception("Commit failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            user_abstraction.create_user(sample_user_data)

        # Verify rollback was called
        assert user_abstraction.db.rollback.called
        assert str(exc_info.value) == "Commit failed"

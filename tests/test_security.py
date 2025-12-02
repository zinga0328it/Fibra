"""
Tests for security module.
"""

import pytest
from datetime import timedelta

from app.security.auth import (
    create_access_token,
    verify_token,
    verify_api_key,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
    
    def test_wrong_password_fails(self):
        """Test that wrong password fails verification."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert not verify_password(wrong_password, hashed)


class TestJWTTokens:
    """Tests for JWT token handling."""
    
    def test_create_and_verify_token(self):
        """Test token creation and verification."""
        subject = "user_123"
        token = create_access_token(subject)
        
        token_data = verify_token(token)
        
        assert token_data is not None
        assert token_data.sub == subject
        assert token_data.type == "access"
    
    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiration."""
        subject = "user_456"
        expires = timedelta(hours=1)
        token = create_access_token(subject, expires_delta=expires)
        
        token_data = verify_token(token)
        
        assert token_data is not None
        assert token_data.sub == subject
    
    def test_invalid_token_returns_none(self):
        """Test that invalid token returns None."""
        invalid_token = "invalid.token.here"
        
        token_data = verify_token(invalid_token)
        
        assert token_data is None


class TestAPIKey:
    """Tests for API key verification."""
    
    def test_verify_api_key_no_key_configured(self, monkeypatch):
        """Test API key verification when no key is configured."""
        from app.config import settings
        monkeypatch.setattr(settings, "api_key", None)
        
        assert verify_api_key("any_key") is True
    
    def test_verify_api_key_correct(self, monkeypatch):
        """Test API key verification with correct key."""
        from app.config import settings
        monkeypatch.setattr(settings, "api_key", "test_api_key")
        
        assert verify_api_key("test_api_key") is True
    
    def test_verify_api_key_incorrect(self, monkeypatch):
        """Test API key verification with incorrect key."""
        from app.config import settings
        monkeypatch.setattr(settings, "api_key", "test_api_key")
        
        assert verify_api_key("wrong_key") is False

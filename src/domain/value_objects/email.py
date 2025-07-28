"""
Email Value Object - Domain Layer

This module contains the Email value object that encapsulates email validation
and business rules following Domain-Driven Design principles.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Email:
    """
    Email value object that ensures email validity and immutability.
    
    This value object follows hexagonal architecture principles by:
    - Being immutable (frozen dataclass)
    - Containing validation logic
    - Being framework-agnostic
    - Encapsulating email-related business rules
    """
    
    value: str
    
    def __post_init__(self):
        """Validate email format on creation."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        if not self.is_valid_format():
            raise ValueError(f"Invalid email format: {self.value}")
        
        if len(self.value) > 254:  # RFC 5321 limit
            raise ValueError("Email address too long (max 254 characters)")
        
        # Convert to lowercase for consistency
        object.__setattr__(self, 'value', self.value.lower().strip())
    
    def is_valid_format(self) -> bool:
        """
        Validate email format using RFC 5322 compliant regex.
        
        Returns:
            bool: True if email format is valid, False otherwise
        """
        # RFC 5322 compliant email regex (simplified but robust)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, self.value):
            return False
        
        # Additional checks
        local_part, domain = self.value.rsplit('@', 1)
        
        # Local part validation
        if len(local_part) > 64:  # RFC 5321 limit
            return False
        
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        
        if '..' in local_part:
            return False
        
        # Domain validation
        if len(domain) > 253:  # RFC 5321 limit
            return False
        
        if domain.startswith('.') or domain.endswith('.'):
            return False
        
        if '..' in domain:
            return False
        
        return True
    
    def get_domain(self) -> str:
        """
        Extract domain part from email.
        
        Returns:
            str: Domain part of the email
        """
        return self.value.split('@')[1]
    
    def get_local_part(self) -> str:
        """
        Extract local part from email.
        
        Returns:
            str: Local part of the email (before @)
        """
        return self.value.split('@')[0]
    
    def is_disposable_email(self) -> bool:
        """
        Check if email is from a known disposable email provider.
        
        Returns:
            bool: True if email is from disposable provider
        """
        # Common disposable email domains
        disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org',
            'throwaway.email', 'getnada.com', 'maildrop.cc',
            'sharklasers.com', 'guerrillamailblock.com'
        }
        
        domain = self.get_domain()
        return domain in disposable_domains
    
    def is_business_email(self) -> bool:
        """
        Check if email appears to be from a business domain.
        
        Returns:
            bool: True if likely business email, False if personal
        """
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'me.com', 'live.com',
            'msn.com', 'yahoo.co.uk', 'googlemail.com'
        }
        
        domain = self.get_domain()
        return domain not in personal_domains
    
    def get_provider(self) -> str:
        """
        Get email provider name.
        
        Returns:
            str: Email provider name
        """
        domain = self.get_domain()
        
        # Map common domains to provider names
        provider_map = {
            'gmail.com': 'Google',
            'googlemail.com': 'Google',
            'yahoo.com': 'Yahoo',
            'yahoo.co.uk': 'Yahoo',
            'hotmail.com': 'Microsoft',
            'outlook.com': 'Microsoft',
            'live.com': 'Microsoft',
            'msn.com': 'Microsoft',
            'aol.com': 'AOL',
            'icloud.com': 'Apple',
            'me.com': 'Apple',
        }
        
        return provider_map.get(domain, domain)
    
    def mask_email(self, show_chars: int = 2) -> str:
        """
        Create a masked version of the email for display purposes.
        
        Args:
            show_chars: Number of characters to show at start of local part
            
        Returns:
            str: Masked email address
        """
        local_part = self.get_local_part()
        domain = self.get_domain()
        
        if len(local_part) <= show_chars:
            masked_local = local_part[0] + '*' * (len(local_part) - 1)
        else:
            masked_local = local_part[:show_chars] + '*' * (len(local_part) - show_chars)
        
        return f"{masked_local}@{domain}"
    
    def to_verification_token_seed(self) -> str:
        """
        Create a seed string for generating verification tokens.
        
        Returns:
            str: Seed string for token generation
        """
        return f"email_verification_{self.value}"
    
    def __str__(self) -> str:
        """String representation of email."""
        return self.value
    
    def __repr__(self) -> str:
        """Detailed string representation of email."""
        return f"Email(value='{self.value}')"
    
    def __eq__(self, other) -> bool:
        """Compare emails for equality."""
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.lower().strip()
        return False
    
    def __hash__(self) -> int:
        """Hash function for email."""
        return hash(self.value)
    
    @classmethod
    def create_if_valid(cls, email_str: str) -> Optional['Email']:
        """
        Create Email instance if valid, return None if invalid.
        
        Args:
            email_str: Email string to validate
            
        Returns:
            Email instance if valid, None if invalid
        """
        try:
            return cls(email_str)
        except ValueError:
            return None
    
    @classmethod
    def is_valid_email_string(cls, email_str: str) -> bool:
        """
        Check if email string is valid without creating instance.
        
        Args:
            email_str: Email string to validate
            
        Returns:
            bool: True if valid email format
        """
        try:
            cls(email_str)
            return True
        except ValueError:
            return False


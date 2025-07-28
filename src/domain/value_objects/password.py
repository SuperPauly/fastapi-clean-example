"""
Password Value Object - Domain Layer

This module contains the Password value object that encapsulates password validation,
hashing, and security rules following Domain-Driven Design principles.
"""

import re
import secrets
import string
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class PasswordStrength(Enum):
    """Password strength levels."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass(frozen=True)
class PasswordPolicy:
    """Password policy configuration."""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    min_special_chars: int = 1
    min_numbers: int = 1
    min_uppercase: int = 1
    min_lowercase: int = 1
    forbidden_patterns: List[str] = None
    
    def __post_init__(self):
        """Initialize forbidden patterns if not provided."""
        if self.forbidden_patterns is None:
            object.__setattr__(self, 'forbidden_patterns', [
                'password', '123456', 'qwerty', 'abc123', 'admin',
                'letmein', 'welcome', 'monkey', 'dragon', 'master'
            ])


@dataclass(frozen=True)
class Password:
    """
    Password value object that ensures password security and immutability.
    
    This value object follows hexagonal architecture principles by:
    - Being immutable (frozen dataclass)
    - Containing validation and security logic
    - Being framework-agnostic
    - Encapsulating password-related business rules
    """
    
    hashed_value: str
    _raw_value: Optional[str] = None  # Only used during creation for validation
    
    def __post_init__(self):
        """Validate password on creation if raw value is provided."""
        if self._raw_value is not None:
            # Validate the raw password
            validation_result = self.validate_password(self._raw_value)
            if not validation_result['is_valid']:
                raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
            
            # Clear raw value after validation for security
            object.__setattr__(self, '_raw_value', None)
    
    @classmethod
    def create_from_raw(cls, raw_password: str, policy: Optional[PasswordPolicy] = None) -> 'Password':
        """
        Create Password instance from raw password string.
        
        Args:
            raw_password: Plain text password
            policy: Password policy to validate against
            
        Returns:
            Password instance with hashed value
        """
        if policy is None:
            policy = PasswordPolicy()
        
        # Create temporary instance for validation
        temp_instance = cls.__new__(cls)
        object.__setattr__(temp_instance, '_raw_value', raw_password)
        object.__setattr__(temp_instance, 'hashed_value', '')
        
        # Validate password
        validation_result = temp_instance.validate_password(raw_password, policy)
        if not validation_result['is_valid']:
            raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
        
        # Hash the password (this would typically use a proper hashing service)
        hashed = cls._hash_password(raw_password)
        
        # Create final instance
        return cls(hashed_value=hashed)
    
    @classmethod
    def create_from_hash(cls, hashed_password: str) -> 'Password':
        """
        Create Password instance from already hashed password.
        
        Args:
            hashed_password: Already hashed password
            
        Returns:
            Password instance
        """
        return cls(hashed_value=hashed_password)
    
    @staticmethod
    def _hash_password(raw_password: str) -> str:
        """
        Hash password using secure algorithm.
        
        Note: In a real implementation, this would use a proper password hashing
        library like bcrypt, scrypt, or Argon2. This is a placeholder.
        
        Args:
            raw_password: Plain text password
            
        Returns:
            Hashed password string
        """
        # This is a placeholder - in real implementation use bcrypt/scrypt/Argon2
        import hashlib
        salt = secrets.token_hex(16)
        return f"$placeholder${salt}${hashlib.pbkdf2_hmac('sha256', raw_password.encode(), salt.encode(), 100000).hex()}"
    
    def verify_password(self, raw_password: str) -> bool:
        """
        Verify raw password against hashed value.
        
        Args:
            raw_password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        # This is a placeholder - in real implementation use proper verification
        try:
            parts = self.hashed_value.split('$')
            if len(parts) != 4 or parts[0] != '' or parts[1] != 'placeholder':
                return False
            
            salt = parts[2]
            stored_hash = parts[3]
            
            import hashlib
            computed_hash = hashlib.pbkdf2_hmac('sha256', raw_password.encode(), salt.encode(), 100000).hex()
            return computed_hash == stored_hash
        except Exception:
            return False
    
    @staticmethod
    def validate_password(password: str, policy: Optional[PasswordPolicy] = None) -> Dict:
        """
        Validate password against policy rules.
        
        Args:
            password: Password to validate
            policy: Password policy to validate against
            
        Returns:
            Dict with validation results
        """
        if policy is None:
            policy = PasswordPolicy()
        
        errors = []
        warnings = []
        
        # Length validation
        if len(password) < policy.min_length:
            errors.append(f"Password must be at least {policy.min_length} characters long")
        
        if len(password) > policy.max_length:
            errors.append(f"Password must be no more than {policy.max_length} characters long")
        
        # Character type validation
        if policy.require_uppercase:
            uppercase_count = sum(1 for c in password if c.isupper())
            if uppercase_count < policy.min_uppercase:
                errors.append(f"Password must contain at least {policy.min_uppercase} uppercase letter(s)")
        
        if policy.require_lowercase:
            lowercase_count = sum(1 for c in password if c.islower())
            if lowercase_count < policy.min_lowercase:
                errors.append(f"Password must contain at least {policy.min_lowercase} lowercase letter(s)")
        
        if policy.require_numbers:
            number_count = sum(1 for c in password if c.isdigit())
            if number_count < policy.min_numbers:
                errors.append(f"Password must contain at least {policy.min_numbers} number(s)")
        
        if policy.require_special:
            special_chars = set(string.punctuation)
            special_count = sum(1 for c in password if c in special_chars)
            if special_count < policy.min_special_chars:
                errors.append(f"Password must contain at least {policy.min_special_chars} special character(s)")
        
        # Forbidden patterns
        password_lower = password.lower()
        for pattern in policy.forbidden_patterns:
            if pattern.lower() in password_lower:
                errors.append(f"Password cannot contain common pattern: {pattern}")
        
        # Common patterns check
        if re.search(r'(.)\1{2,}', password):
            warnings.append("Password contains repeated characters")
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            warnings.append("Password contains sequential numbers")
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            warnings.append("Password contains sequential letters")
        
        # Calculate strength
        strength = Password.calculate_strength(password)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'strength': strength,
            'score': Password._calculate_score(password)
        }
    
    @staticmethod
    def calculate_strength(password: str) -> PasswordStrength:
        """
        Calculate password strength based on various factors.
        
        Args:
            password: Password to analyze
            
        Returns:
            PasswordStrength enum value
        """
        score = Password._calculate_score(password)
        
        if score < 20:
            return PasswordStrength.VERY_WEAK
        elif score < 40:
            return PasswordStrength.WEAK
        elif score < 60:
            return PasswordStrength.FAIR
        elif score < 80:
            return PasswordStrength.GOOD
        elif score < 90:
            return PasswordStrength.STRONG
        else:
            return PasswordStrength.VERY_STRONG
    
    @staticmethod
    def _calculate_score(password: str) -> int:
        """
        Calculate numerical password strength score.
        
        Args:
            password: Password to score
            
        Returns:
            int: Score from 0-100
        """
        score = 0
        
        # Length bonus
        score += min(len(password) * 2, 25)
        
        # Character variety bonus
        if any(c.islower() for c in password):
            score += 5
        if any(c.isupper() for c in password):
            score += 5
        if any(c.isdigit() for c in password):
            score += 5
        if any(c in string.punctuation for c in password):
            score += 10
        
        # Unique characters bonus
        unique_chars = len(set(password))
        score += min(unique_chars * 2, 20)
        
        # Entropy bonus
        if len(password) > 0:
            char_frequency = {}
            for char in password:
                char_frequency[char] = char_frequency.get(char, 0) + 1
            
            entropy = 0
            for count in char_frequency.values():
                probability = count / len(password)
                if probability > 0:
                    entropy -= probability * (probability.bit_length() - 1)
            
            score += min(int(entropy * 10), 20)
        
        # Penalties
        # Repeated characters
        if re.search(r'(.)\1{2,}', password):
            score -= 10
        
        # Sequential patterns
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            score -= 10
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            score -= 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def generate_secure_password(
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_special: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """
        Generate a cryptographically secure password.
        
        Args:
            length: Password length
            include_uppercase: Include uppercase letters
            include_lowercase: Include lowercase letters
            include_numbers: Include numbers
            include_special: Include special characters
            exclude_ambiguous: Exclude ambiguous characters (0, O, l, 1, etc.)
            
        Returns:
            Generated password string
        """
        chars = ""
        
        if include_lowercase:
            chars += string.ascii_lowercase
        if include_uppercase:
            chars += string.ascii_uppercase
        if include_numbers:
            chars += string.digits
        if include_special:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if exclude_ambiguous:
            ambiguous = "0O1lI|`"
            chars = ''.join(c for c in chars if c not in ambiguous)
        
        if not chars:
            raise ValueError("No character types selected for password generation")
        
        # Ensure at least one character from each selected type
        password = []
        
        if include_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))
        if include_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))
        if include_numbers:
            password.append(secrets.choice(string.digits))
        if include_special:
            password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
        
        # Fill remaining length
        for _ in range(length - len(password)):
            password.append(secrets.choice(chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def is_expired(self, max_age_days: int) -> bool:
        """
        Check if password has expired based on age.
        
        Note: This would require storing password creation date,
        which is not implemented in this basic version.
        
        Args:
            max_age_days: Maximum password age in days
            
        Returns:
            bool: True if password is expired
        """
        # Placeholder - would need password creation timestamp
        return False
    
    def __str__(self) -> str:
        """String representation (masked for security)."""
        return "[PROTECTED]"
    
    def __repr__(self) -> str:
        """Detailed string representation (masked for security)."""
        return "Password(hashed_value='[PROTECTED]')"
    
    def __eq__(self, other) -> bool:
        """Compare passwords for equality."""
        if isinstance(other, Password):
            return self.hashed_value == other.hashed_value
        return False
    
    def __hash__(self) -> int:
        """Hash function for password."""
        return hash(self.hashed_value)


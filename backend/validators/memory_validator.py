"""
Memory Content Validation System
Validates content quality, structure, and metadata before storage
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class MemoryValidationError(Exception):
    """Raised when memory validation fails"""
    pass


class ValidationResult(BaseModel):
    """Result of validation check"""
    is_valid: bool
    score: float = Field(ge=0.0, le=1.0)  # 0-1 quality score
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class MemoryValidator:
    """
    Validates memory content before storage

    Checks:
    - Content quality (length, structure, language)
    - Metadata schema
    - Duplicate detection sensitivity
    - Security (no secrets, PII)
    """

    # Regex patterns for security checks
    SECRETS_PATTERNS = [
        r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})",
        r"(?:secret[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})",
        r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})",
        r"(?:token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{32,})",
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        r"sk_live_[a-zA-Z0-9]{24,}",  # Stripe secret key
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub personal token
    ]

    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN (US)
        r"\b\d{16}\b",  # Credit card (simple)
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",  # Email
    ]

    # Required metadata fields
    REQUIRED_METADATA = ["source_type"]

    # Allowed source types
    ALLOWED_SOURCE_TYPES = [
        "conversation", "document", "code", "task",
        "system", "api", "user", "agent", "rule", "memory"
    ]

    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 10000,
        check_secrets: bool = True,
        check_pii: bool = False,
        strict_mode: bool = False
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.check_secrets = check_secrets
        self.check_pii = check_pii
        self.strict_mode = strict_mode

    def validate_content(self, content: str) -> ValidationResult:
        """
        Validate content quality and structure

        Args:
            content: Text content to validate

        Returns:
            ValidationResult with score and issues
        """
        errors = []
        warnings = []
        suggestions = []
        score = 1.0

        # 1. Length checks
        if not content or len(content.strip()) == 0:
            errors.append("Content is empty")
            return ValidationResult(is_valid=False, score=0.0, errors=errors)

        content_len = len(content)

        if content_len < self.min_length:
            errors.append(f"Content too short ({content_len} < {self.min_length} chars)")
            score -= 0.3

        if content_len > self.max_length:
            errors.append(f"Content too long ({content_len} > {self.max_length} chars)")
            score -= 0.2

        # 2. Quality checks
        word_count = len(content.split())
        if word_count < 3:
            warnings.append("Very few words, consider adding more context")
            score -= 0.1

        # Check for repetitive content
        words = content.lower().split()
        if words and len(set(words)) / len(words) < 0.3:
            warnings.append("Content appears highly repetitive")
            score -= 0.2

        # Check for excessive punctuation/special chars
        special_chars = len(re.findall(r"[^a-zA-Z0-9\s]", content))
        if special_chars / content_len > 0.3:
            warnings.append("High ratio of special characters")
            score -= 0.1

        # 3. Security checks
        if self.check_secrets:
            for pattern in self.SECRETS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    errors.append("Content contains potential secret/API key")
                    score -= 0.5
                    break

        if self.check_pii:
            for pattern in self.PII_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    warnings.append("Content may contain PII (email, SSN, etc.)")
                    score -= 0.2
                    break

        # 4. Structure suggestions
        if content_len > 500 and "\n" not in content:
            suggestions.append("Consider adding line breaks for better readability")

        if content.isupper():
            suggestions.append("Content is all uppercase, consider mixed case")

        # Final validation
        is_valid = len(errors) == 0 if self.strict_mode else score >= 0.3
        score = max(0.0, min(1.0, score))

        return ValidationResult(
            is_valid=is_valid,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_metadata(
        self,
        metadata: Optional[Dict[str, Any]],
        source_type: str
    ) -> ValidationResult:
        """
        Validate metadata structure and content

        Args:
            metadata: Metadata dict
            source_type: Source type string

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        suggestions = []
        score = 1.0

        # 1. Source type validation
        if source_type not in self.ALLOWED_SOURCE_TYPES:
            errors.append(f"Invalid source_type: {source_type}")
            score -= 0.3

        # 2. Metadata presence
        if not metadata or metadata == {}:
            warnings.append("No metadata provided")
            suggestions.append("Add tags or categories for better retrieval")
            score -= 0.1
        else:
            # Check for useful metadata
            if "tags" not in metadata:
                suggestions.append("Consider adding tags for categorization")

            if "tags" in metadata:
                tags = metadata["tags"]
                if isinstance(tags, list):
                    if len(tags) == 0:
                        warnings.append("Tags list is empty")
                    elif len(tags) > 10:
                        warnings.append("Too many tags (>10), consider consolidating")
                        score -= 0.1
                else:
                    errors.append("Tags must be a list")
                    score -= 0.2

        is_valid = len(errors) == 0 if self.strict_mode else score >= 0.5
        score = max(0.0, min(1.0, score))

        return ValidationResult(
            is_valid=is_valid,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
        source_type: str
    ) -> Tuple[bool, ValidationResult]:
        """
        Complete validation of memory before storage

        Args:
            content: Text content
            metadata: Metadata dict
            source_type: Source type

        Returns:
            Tuple of (is_valid, combined_result)
        """
        # Validate content
        content_result = self.validate_content(content)

        # Validate metadata
        metadata_result = self.validate_metadata(metadata, source_type)

        # Combine results
        combined_errors = content_result.errors + metadata_result.errors
        combined_warnings = content_result.warnings + metadata_result.warnings
        combined_suggestions = content_result.suggestions + metadata_result.suggestions

        # Average scores
        combined_score = (content_result.score + metadata_result.score) / 2

        # Overall validity
        is_valid = content_result.is_valid and metadata_result.is_valid

        combined_result = ValidationResult(
            is_valid=is_valid,
            score=combined_score,
            errors=combined_errors,
            warnings=combined_warnings,
            suggestions=combined_suggestions
        )

        return is_valid, combined_result


# Global validator instance
default_validator = MemoryValidator(
    min_length=10,
    max_length=10000,
    check_secrets=True,
    check_pii=False,
    strict_mode=False
)

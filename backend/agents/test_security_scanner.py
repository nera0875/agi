"""
Unit tests for SecurityScanner
"""

import pytest
from pathlib import Path
from backend.agents.security_scanner import SecurityScanner


class TestSecurityScanner:
    """Test security pattern detection"""

    def test_scanner_initialization(self):
        """Test scanner can be initialized"""
        scanner = SecurityScanner()
        assert scanner is not None
        assert len(scanner.CRITICAL_PATTERNS) == 11
        assert len(scanner.SENSITIVE_FILES) == 10

    def test_statistics(self):
        """Test scanner statistics"""
        scanner = SecurityScanner()
        stats = scanner.get_statistics()

        assert stats['critical_patterns'] == 11
        assert stats['sensitive_files'] == 10
        assert stats['ban_phrases'] == 2

    def test_critical_patterns_exist(self):
        """Test that critical patterns are defined"""
        scanner = SecurityScanner()

        expected_patterns = [
            'api_key_anthropic',
            'api_key_voyage',
            'api_key_cohere',
            'generic_api_key',
            'secret_key',
            'password_hardcoded',
            'aws_secret',
            'db_url',
            'private_key_pem',
            'private_key_rsa',
            'token_jwt',
        ]

        for pattern_name in expected_patterns:
            assert pattern_name in scanner.CRITICAL_PATTERNS

    def test_sensitive_files_list(self):
        """Test sensitive files patterns"""
        scanner = SecurityScanner()

        # Should have patterns for sensitive files
        assert len(scanner.SENSITIVE_FILES) > 0

        # Check some key patterns exist
        patterns_str = str(scanner.SENSITIVE_FILES)
        assert 'env' in patterns_str.lower()
        assert 'secret' in patterns_str.lower()
        assert 'key' in patterns_str.lower()

    def test_ban_phrases(self):
        """Test ban phrases are set"""
        scanner = SecurityScanner()

        assert 'Voiture789' in scanner.BAN_PHRASES
        assert 'sk-ant-' in scanner.BAN_PHRASES

    def test_method_scan_staged_changes_exists(self):
        """Test scan_staged_changes method exists"""
        scanner = SecurityScanner()
        assert hasattr(scanner, 'scan_staged_changes')
        assert callable(scanner.scan_staged_changes)

    def test_method_scan_file_exists(self):
        """Test scan_file method exists"""
        scanner = SecurityScanner()
        assert hasattr(scanner, 'scan_file')
        assert callable(scanner.scan_file)

    def test_detection_returns_dict(self):
        """Test that methods return dict"""
        scanner = SecurityScanner()

        # scan_file with non-existent file should return dict
        result = scanner.scan_file(Path("/nonexistent/file.py"))
        assert isinstance(result, dict)
        assert 'status' in result

    def test_anthropic_key_pattern_valid(self):
        """Test anthropic key pattern is valid regex"""
        import re

        scanner = SecurityScanner()
        pattern = scanner.CRITICAL_PATTERNS['api_key_anthropic']

        # Should match valid pattern
        valid = 'ANTHROPIC_API_KEY = sk-ant-xyz123abc'
        assert re.search(pattern, valid, re.IGNORECASE)

    def test_database_url_pattern_valid(self):
        """Test database URL pattern is valid regex"""
        import re

        scanner = SecurityScanner()
        pattern = scanner.CRITICAL_PATTERNS['db_url']

        # Should match connection string with credentials
        valid = 'DATABASE_URL=postgresql://user:password@localhost/db'
        assert re.search(pattern, valid, re.IGNORECASE)

    def test_password_pattern_valid(self):
        """Test password pattern is valid regex"""
        import re

        scanner = SecurityScanner()
        pattern = scanner.CRITICAL_PATTERNS['password_hardcoded']

        # Should match hardcoded password
        valid = 'PASSWORD = "MySecret123"'
        assert re.search(pattern, valid, re.IGNORECASE)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

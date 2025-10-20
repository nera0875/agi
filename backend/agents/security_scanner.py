"""
Security Scanner for Pre-Commit Hook Integration
Companion to git pre-commit hook - used for deep security analysis
"""

import re
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple


class SecurityScanner:
    """Fast security pattern detection for git pre-commit"""

    CRITICAL_PATTERNS = {
        'api_key_anthropic': r'ANTHROPIC_API_KEY\s*=.*sk-ant-',
        'api_key_voyage': r'VOYAGE_API_KEY\s*=.*["\047]',
        'api_key_cohere': r'COHERE_API_KEY\s*=.*["\047]',
        'generic_api_key': r'API_KEY\s*=\s*["\047][^"]{10,}["\047]',
        'secret_key': r'SECRET_KEY\s*=\s*["\047][^"]+["\047]',
        'password_hardcoded': r'(?:PASSWORD|pwd)\s*=\s*["\047][^"]+["\047]',
        'aws_secret': r'AWS_SECRET_ACCESS_KEY',
        'db_url': r'DATABASE_URL.*://.*:.*@',
        'private_key_pem': r'-----BEGIN PRIVATE KEY-----',
        'private_key_rsa': r'-----BEGIN RSA PRIVATE KEY-----',
        'token_jwt': r'eyJhbGciOi[A-Za-z0-9_-]{100,}',
    }

    SENSITIVE_FILES = [
        r'\.env$',
        r'\.env\.',
        r'secrets\.',
        r'credentials\.',
        r'\.pem$',
        r'\.key$',
        r'\.p12$',
        r'\.pfx$',
        r'config\.prod',
        r'settings\.prod',
    ]

    BAN_PHRASES = [
        'Voiture789',  # VPS root password
        'sk-ant-',     # Anthropic keys pattern
    ]

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()

    def scan_staged_changes(self) -> Dict:
        """Scan git staged changes for security issues"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            diff_content = result.stdout
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

        if not diff_content:
            return {'status': 'clean', 'findings': []}

        findings = []

        # Check patterns
        for name, pattern in self.CRITICAL_PATTERNS.items():
            matches = re.finditer(pattern, diff_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                findings.append({
                    'type': 'pattern',
                    'severity': 'critical',
                    'name': name,
                    'line': diff_content[:match.start()].count('\n') + 1,
                    'excerpt': match.group(0)[:50]
                })

        # Check sensitive files
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            files = result.stdout.strip().split('\n')
        except Exception:
            files = []

        for filepath in files:
            for pattern in self.SENSITIVE_FILES:
                if re.search(pattern, filepath):
                    findings.append({
                        'type': 'sensitive_file',
                        'severity': 'critical',
                        'file': filepath,
                        'pattern': pattern
                    })

        # Check ban phrases
        for phrase in self.BAN_PHRASES:
            if phrase in diff_content:
                findings.append({
                    'type': 'banned_phrase',
                    'severity': 'critical',
                    'phrase': phrase
                })

        return {
            'status': 'issues_found' if findings else 'clean',
            'findings': findings,
            'count': len(findings)
        }

    def scan_file(self, filepath: Path) -> Dict:
        """Scan single file for security issues"""
        try:
            content = filepath.read_text(errors='ignore')
        except Exception as e:
            return {'status': 'error', 'file': str(filepath), 'message': str(e)}

        findings = []

        for name, pattern in self.CRITICAL_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                findings.append({
                    'type': 'pattern',
                    'severity': 'critical',
                    'name': name,
                    'line': line_num,
                    'file': str(filepath)
                })

        return {
            'status': 'issues_found' if findings else 'clean',
            'file': str(filepath),
            'findings': findings
        }

    def get_statistics(self) -> Dict:
        """Get security statistics"""
        return {
            'critical_patterns': len(self.CRITICAL_PATTERNS),
            'sensitive_files': len(self.SENSITIVE_FILES),
            'ban_phrases': len(self.BAN_PHRASES),
            'detection_time_ms': '<100ms (typical)'
        }


def main():
    """CLI entry point"""
    import sys

    scanner = SecurityScanner()
    result = scanner.scan_staged_changes()

    print(json.dumps(result, indent=2))

    if result.get('status') == 'issues_found':
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()

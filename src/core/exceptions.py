"""
Custom exceptions for Qualys Automation
"""


class QualysAutomationError(Exception):
    """Base exception for Qualys Automation"""
    pass


class ConfigurationError(QualysAutomationError):
    """Raised when there's a configuration error"""
    pass


class APIError(QualysAutomationError):
    """Raised when there's an API communication error"""
    pass


class AuthenticationError(APIError):
    """Raised when authentication fails"""
    pass


class ParsingError(QualysAutomationError):
    """Raised when parsing fails (XML, CSV, etc.)"""
    pass


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


class DatabaseError(QualysAutomationError):
    """Raised when there's a database error"""
    pass


class ParsingError(QualysAutomationError):
    """Raised when parsing fails (XML, CSV, etc.)"""
    pass


class ValidationError(QualysAutomationError):
    """Raised when data validation fails"""
    pass


class ReportError(QualysAutomationError):
    """Raised when report generation or processing fails"""
    pass
"""
Base domain exception.
"""


class DomainException(Exception):
    """
    Base exception for all domain errors.
    Use this as the base for all custom exceptions.
    """
    
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message

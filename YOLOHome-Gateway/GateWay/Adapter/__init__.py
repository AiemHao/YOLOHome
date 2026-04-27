"""
Adapter Module - Data format conversion layer
Export public interfaces
"""

from .base import DataAdapter
from .default_adapter import DefaultDataAdapter
from .registry import get_default_adapter, set_adapter, get_adapter, reset_adapter

__all__ = [
    # Base class
    'DataAdapter',
    
    # Implementations
    'DefaultDataAdapter',
    
    # Registry functions (Singleton)
    'get_default_adapter',
    'set_adapter',
    'get_adapter',
    'reset_adapter',
]

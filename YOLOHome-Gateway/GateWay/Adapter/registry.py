"""
Adapter Registry - Quản lý global adapter instance (Singleton pattern)
"""

from typing import Optional, Dict
from .base import DataAdapter


# Global adapter instance
_adapter_instance: Optional[DataAdapter] = None


def get_default_adapter(device_mapping: Dict[str, str] = None) -> DataAdapter:
    """
    Lấy adapter instance mặc định (Singleton)
    
    Tạo DefaultDataAdapter nếu chưa tồn tại
    
    Args:
        device_mapping: Optional device mapping dict
                       Chỉ sử dụng khi tạo instance mới
    
    Returns:
        DataAdapter instance
    """
    global _adapter_instance
    
    if _adapter_instance is None:
        from .default_adapter import DefaultDataAdapter
        _adapter_instance = DefaultDataAdapter(device_mapping=device_mapping)
    
    return _adapter_instance


def set_adapter(adapter: DataAdapter) -> None:
    """
    Đặt adapter toàn cục
    
    Args:
        adapter: DataAdapter instance để sử dụng
    """
    global _adapter_instance
    _adapter_instance = adapter


def get_adapter() -> DataAdapter:
    """Alias của get_default_adapter() - lấy adapter hiện tại"""
    return get_default_adapter()


def reset_adapter() -> None:
    """Reset adapter về None (sẽ tạo mới lần tiếp theo)"""
    global _adapter_instance
    _adapter_instance = None

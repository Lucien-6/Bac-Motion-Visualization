"""
Object visibility manager.

Manages object hiding and truncation operations for visualization.
"""

from dataclasses import dataclass
from typing import Literal

from PyQt6.QtCore import QObject, pyqtSignal

from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class HiddenRecord:
    """Record of a hidden object operation."""
    obj_id: int
    mode: Literal['before', 'after']
    frame: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'obj_id': self.obj_id,
            'mode': self.mode,
            'frame': self.frame,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HiddenRecord':
        """Create from dictionary."""
        return cls(
            obj_id=data['obj_id'],
            mode=data['mode'],
            frame=data['frame'],
        )
    
    def get_description(self) -> str:
        """Get human-readable description."""
        if self.mode == 'before':
            return f"Object {self.obj_id}: hidden at frame ≤{self.frame}"
        else:
            return f"Object {self.obj_id}: hidden at frame ≥{self.frame}"


class ObjectManager(QObject):
    """
    Manages object visibility state for visualization.
    
    Allows hiding objects before or after specific frames,
    with undo capability.
    
    Signals:
        records_changed: Emitted when hidden records change.
    """
    
    records_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize object manager."""
        super().__init__(parent)
        self._hidden_records: list[HiddenRecord] = []
    
    def hide_object_before(self, obj_id: int, frame: int):
        """
        Hide an object at and before a specific frame.
        
        Args:
            obj_id: Object ID to hide.
            frame: Frame threshold (inclusive).
        """
        self._remove_existing_record(obj_id)
        
        record = HiddenRecord(obj_id=obj_id, mode='before', frame=frame)
        self._hidden_records.append(record)
        
        logger.info(f"Object {obj_id} hidden at frame <= {frame}")
        self.records_changed.emit()
    
    def hide_object_after(self, obj_id: int, frame: int):
        """
        Hide an object at and after a specific frame.
        
        Args:
            obj_id: Object ID to hide.
            frame: Frame threshold (inclusive).
        """
        self._remove_existing_record(obj_id)
        
        record = HiddenRecord(obj_id=obj_id, mode='after', frame=frame)
        self._hidden_records.append(record)
        
        logger.info(f"Object {obj_id} hidden at frame >= {frame}")
        self.records_changed.emit()
    
    def _remove_existing_record(self, obj_id: int):
        """Remove any existing record for an object."""
        self._hidden_records = [
            r for r in self._hidden_records if r.obj_id != obj_id
        ]
    
    def restore_object(self, obj_id: int):
        """
        Restore a hidden object.
        
        Args:
            obj_id: Object ID to restore.
        """
        before_count = len(self._hidden_records)
        self._remove_existing_record(obj_id)
        
        if len(self._hidden_records) < before_count:
            logger.info(f"Object {obj_id} restored")
            self.records_changed.emit()
    
    def restore_all(self):
        """Restore all hidden objects."""
        if self._hidden_records:
            self._hidden_records.clear()
            logger.info("All objects restored")
            self.records_changed.emit()
    
    def is_visible(self, obj_id: int, frame: int) -> bool:
        """
        Check if an object is visible at a specific frame.
        
        Args:
            obj_id: Object ID.
            frame: Frame index.
            
        Returns:
            True if visible, False if hidden.
        """
        for record in self._hidden_records:
            if record.obj_id == obj_id:
                if record.mode == 'before' and frame <= record.frame:
                    return False
                elif record.mode == 'after' and frame >= record.frame:
                    return False
        
        return True
    
    def get_hidden_records(self) -> list[HiddenRecord]:
        """
        Get list of all hidden records.
        
        Returns:
            List of HiddenRecord objects.
        """
        return self._hidden_records.copy()
    
    def get_hidden_object_ids(self) -> list[int]:
        """
        Get list of object IDs that have hidden records.
        
        Returns:
            List of object IDs.
        """
        return [r.obj_id for r in self._hidden_records]
    
    def has_hidden_objects(self) -> bool:
        """Check if there are any hidden objects."""
        return len(self._hidden_records) > 0
    
    def get_record_for_object(self, obj_id: int) -> HiddenRecord | None:
        """
        Get hidden record for a specific object.
        
        Args:
            obj_id: Object ID.
            
        Returns:
            HiddenRecord or None if not hidden.
        """
        for record in self._hidden_records:
            if record.obj_id == obj_id:
                return record
        return None
    
    def to_list(self) -> list[dict]:
        """Convert all records to list of dictionaries."""
        return [r.to_dict() for r in self._hidden_records]
    
    def from_list(self, data: list[dict]):
        """Load records from list of dictionaries."""
        self._hidden_records = [
            HiddenRecord.from_dict(d) for d in data
        ]
        self.records_changed.emit()

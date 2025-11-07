"""
Transfer State Manager for ImageKit Plugin

Tracks active file transfers and handles cleanup.
"""

import logging
import uuid
from datetime import datetime, timedelta

from mcp_remote_exec.plugins.imagekit.models import TransferState, TransferOperation

_log = logging.getLogger(__name__)


class TransferManager:
    """Manages active file transfer states"""

    def __init__(self, timeout_seconds: int = 3600):
        """
        Initialize transfer manager.

        Args:
            timeout_seconds: Transfer timeout in seconds (default: 3600 = 1 hour)
        """
        self.timeout_seconds = timeout_seconds
        self._transfers: dict[str, TransferState] = {}

    def create_transfer(
        self,
        operation: TransferOperation,
        remote_path: str,
        permissions: int | None = None,
        overwrite: bool = False,
        ctid: int | None = None,
    ) -> TransferState:
        """
        Create a new transfer state.

        Args:
            operation: Upload or download
            remote_path: Path on remote server (or in container if ctid is set)
            permissions: Optional file permissions
            overwrite: Whether to overwrite existing file
            ctid: Optional Proxmox container ID for auto-push after upload

        Returns:
            TransferState with generated transfer_id
        """
        transfer_id = str(uuid.uuid4())

        state = TransferState(
            transfer_id=transfer_id,
            operation=operation,
            remote_path=remote_path,
            timestamp=datetime.now(),
            permissions=permissions,
            overwrite=overwrite,
            ctid=ctid,
        )

        self._transfers[transfer_id] = state
        _log.debug(
            f"Created {operation.value} transfer {transfer_id} for {remote_path}"
        )

        return state

    def get_transfer(self, transfer_id: str) -> TransferState | None:
        """
        Get transfer state by ID.

        Args:
            transfer_id: Transfer identifier

        Returns:
            TransferState if found, None otherwise
        """
        return self._transfers.get(transfer_id)

    def update_transfer(
        self, transfer_id: str, imagekit_file_id: str | None = None
    ) -> bool:
        """
        Update transfer state.

        Args:
            transfer_id: Transfer identifier
            imagekit_file_id: ImageKit file ID

        Returns:
            True if transfer was found and updated, False otherwise
        """
        transfer = self._transfers.get(transfer_id)
        if not transfer:
            return False

        if imagekit_file_id is not None:
            transfer.imagekit_file_id = imagekit_file_id

        _log.debug(f"Updated transfer {transfer_id}")
        return True

    def complete_transfer(self, transfer_id: str) -> TransferState | None:
        """
        Mark transfer as complete and remove from state.

        Args:
            transfer_id: Transfer identifier

        Returns:
            TransferState if found, None otherwise
        """
        transfer = self._transfers.pop(transfer_id, None)
        if transfer:
            _log.debug(f"Completed {transfer.operation} transfer {transfer_id}")
        else:
            _log.warning(f"Transfer {transfer_id} not found")

        return transfer

    def cleanup_expired_transfers(self) -> int:
        """
        Remove transfers older than timeout.

        Returns:
            Number of expired transfers removed
        """
        cutoff_time = datetime.now() - timedelta(seconds=self.timeout_seconds)
        expired_ids = [
            tid
            for tid, transfer in self._transfers.items()
            if transfer.timestamp < cutoff_time
        ]

        for tid in expired_ids:
            transfer = self._transfers.pop(tid)
            _log.info(f"Cleaned up expired {transfer.operation} transfer {tid}")

        return len(expired_ids)

    def get_active_count(self) -> int:
        """Get count of active transfers"""
        return len(self._transfers)

    def clear_all(self) -> None:
        """Clear all transfers (for testing/cleanup)"""
        count = len(self._transfers)
        self._transfers.clear()
        _log.debug(f"Cleared {count} transfers")

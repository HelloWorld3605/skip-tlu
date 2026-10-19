from abc import ABC, abstractmethod
from skiptlu.models.activity import Activity, CompletionStatus


class ActivityHandler(ABC):
    @abstractmethod
    async def execute(self, activity: Activity) -> CompletionStatus:
        """Perform the minimum valid workflow for this activity."""

    @abstractmethod
    async def verify(self, activity: Activity) -> CompletionStatus:
        """Re-read server state and return the authoritative status."""

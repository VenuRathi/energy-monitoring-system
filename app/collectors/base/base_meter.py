from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseMeter(ABC):
    """Common interface for any energy meter collector driver."""

    @abstractmethod
    def read_all(self) -> Dict[str, Optional[object]]:
        """Read all configured parameters from a meter."""
        raise NotImplementedError


"""
## FILE EXPLANATION
Purpose:
This file defines a base contract for all meter drivers.

Why this file exists:
Different meter models should follow one common method signature,
so services can call all drivers in a uniform way.

What data enters the file:
No runtime meter data enters directly. Child classes implement the logic.

What data leaves the file:
A typed method contract: read_all() -> dictionary of readings.

Which layer of the architecture it belongs to:
Collector Layer (base abstractions).

How it interacts with other files:
Used by collector driver files such as schneider/pm5000.py and by
service files that depend on a common driver interface.
"""

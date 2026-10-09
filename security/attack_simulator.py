"""Generate invalid route proposals without changing any network state."""

from typing import List
from network.manager import NetworkManager
from .threat_detector import ClientState


def unauthorized_route(manager: NetworkManager, client: ClientState) -> List[str]:
    """Use a guaranteed nonexistent router, displayed only as a blocked overlay."""
    rogue = "Unauthorized X"
    while rogue in manager.base_graph:
        rogue += "X"
    return [client.source, rogue, client.destination]

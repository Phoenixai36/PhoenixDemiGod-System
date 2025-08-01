"""
Example usage of Podman client and event listener.
"""

import asyncio
import logging
from datetime import datetime

from .podman_client import PodmanClient, PodmanConfig
from .event_listener import ContainerEventListener, EventListenerConfig, EventType
from .models import ContainerEvent


async def basic_example():
    """Basic Podman client example."""
    print("=== Basic Podman Example ===")
    
    config = PodmanConfig(auto_detect=True, fallback_to_docker=True)
    
    async with PodmanClient(config) as client:
        # Get version
        version = await client.get_version()
        print(f"Runtime version: {version}")
        
        # List containers
        containers = await client.list_containers()
        print(f"Found {len(containers)} containers")
        
        for container in containers:
            print(f"  - {container.name}: {container.status.value}")


async def event_example():
    """Event listening example."""
    print("\n=== Event Listening Example ===")
    
    config = EventListenerConfig(
        event_types={EventType.CONTAINER_START, EventType.CONTAINER_STOP},
        event_batch_timeout=1.0
    )
    
    listener = ContainerEventListener(config)
    
    def event_handler(event: ContainerEvent):
        print(f"Event: {event.action} - {event.container_name}")
    
    listener.add_event_handler(event_handler)
    
    try:
        await listener.start()
        print("Listening for events for 10 seconds...")
        await asyncio.sleep(10)
    finally:
        await listener.stop()


async def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        await basic_example()
        await event_example()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
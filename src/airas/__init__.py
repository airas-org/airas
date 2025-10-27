from airas.services.api_client.api_clients_container import api_clients_container

# Wire the container to enable dependency injection across the package
# This must be called before any @inject decorated functions are used
api_clients_container.wire(packages=["airas.features"])

__all__ = ["api_clients_container"]

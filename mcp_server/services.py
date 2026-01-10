"""Service registry for dependency injection.

This module provides a central registry for managing service dependencies
throughout the MCP server. It implements the Service Locator pattern with
dependency injection support.
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar

from .config import Config, get_config
from .exceptions import PPTXError


T = TypeVar('T')


class ServiceRegistry:
    """Central registry for managing service dependencies.
    
    This class implements a simple dependency injection container that allows
    registering and resolving service instances throughout the application.
    
    Example:
        # Register services
        registry = ServiceRegistry()
        registry.register(ILogger, get_logger(__name__))
        registry.register(ICache, LRUCache(maxsize=100))
        
        # Resolve services
        logger = registry.resolve(ILogger)
        cache = registry.resolve(ICache)
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize service registry.
        
        Args:
            config: Optional configuration. If None, uses global config.
        """
        self._services: Dict[type, Any] = {}
        self._factories: Dict[type, Callable[[], Any]] = {}
        self._singletons: Dict[type, Any] = {}
        self._config = config or get_config()
    
    @property
    def config(self) -> Config:
        """Get the configuration."""
        return self._config
    
    def register(
        self,
        service_type: Type[T],
        service_instance: T,
        singleton: bool = True
    ) -> None:
        """Register a service instance.
        
        Args:
            service_type: The type/interface of the service
            service_instance: The service instance
            singleton: If True, the same instance is returned on every resolve
            
        Example:
            registry.register(ILogger, get_logger(__name__))
        """
        if singleton:
            self._singletons[service_type] = service_instance
        else:
            self._services[service_type] = service_instance
    
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        singleton: bool = False
    ) -> None:
        """Register a service factory.
        
        The factory will be called to create a service instance when needed.
        
        Args:
            service_type: The type/interface of the service
            factory: Factory function that creates the service
            singleton: 
                - If True, the factory is called immediately and the created
                  instance is stored as a singleton. All subsequent
                  :meth:`resolve` calls for this type will return that
                  pre-created instance.
                - If False (default), the factory itself is stored and will
                  be called on every :meth:`resolve` to create a new instance.
            
        Example:
            # Non-singleton: new instance on each resolve
            registry.register_factory(
                IPPTXHandler,
                lambda: PPTXHandler(path),
                singleton=False
            )
            
            # Eager singleton: instance is created immediately and reused
            registry.register_factory(
                IPPTXHandler,
                lambda: PPTXHandler(path),
                singleton=True
            )
        """
        self._factories[service_type] = factory
        if singleton:
            # Eagerly pre-create and cache singleton instance
            self._singletons[service_type] = factory()
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance.
        
        Args:
            service_type: The type/interface of the service to resolve
            
        Returns:
            The service instance
            
        Raises:
            PPTXError: If service is not registered
            
        Example:
            logger = registry.resolve(ILogger)
        """
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Check regular services
        if service_type in self._services:
            return self._services[service_type]
        
        # Check factories
        if service_type in self._factories:
            return self._factories[service_type]()
        
        # Service not found
        raise PPTXError(
            f"Service not registered: {service_type.__name__}",
            details={"service_type": str(service_type)}
        )
    
    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service instance or return None if not registered.
        
        Args:
            service_type: The type/interface of the service to resolve
            
        Returns:
            The service instance or None if not registered
            
        Example:
            cache = registry.resolve_optional(ICache)
            if cache:
                cache.set("key", value)
        """
        try:
            return self.resolve(service_type)
        except PPTXError:
            return None
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered.
        
        Args:
            service_type: The type/interface to check
            
        Returns:
            True if registered, False otherwise
        """
        return (
            service_type in self._singletons or
            service_type in self._services or
            service_type in self._factories
        )
    
    def unregister(self, service_type: Type) -> None:
        """Unregister a service.
        
        Args:
            service_type: The type/interface to unregister
        """
        self._singletons.pop(service_type, None)
        self._services.pop(service_type, None)
        self._factories.pop(service_type, None)
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._singletons.clear()
        self._services.clear()
        self._factories.clear()
    
    def get_registered_services(self) -> list[Type]:
        """Get list of all registered service types.
        
        Returns:
            List of registered service types
        """
        services = set()
        services.update(self._singletons.keys())
        services.update(self._services.keys())
        services.update(self._factories.keys())
        return list(services)


# Global service registry instance
_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    """Get the global service registry.
    
    Returns:
        The global ServiceRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry


def set_registry(registry: ServiceRegistry) -> None:
    """Set the global service registry.
    
    Args:
        registry: The registry to set as global
    """
    global _registry
    _registry = registry


def reset_registry() -> None:
    """Reset the global service registry (useful for testing)."""
    global _registry
    _registry = None


def setup_default_services(registry: Optional[ServiceRegistry] = None) -> ServiceRegistry:
    """Setup default services in the registry.
    
    This function registers default implementations for common services.
    
    Args:
        registry: Optional registry to use. If None, uses global registry.
        
    Returns:
        The configured ServiceRegistry
    """
    if registry is None:
        registry = get_registry()
    
    # Access config to ensure it is initialized / available
    registry.config
    
    # Register logger factory
    from .logging_config import get_logger
    registry.register_factory(
        type(get_logger(__name__)),
        lambda: get_logger("mcp_server"),
        singleton=True
    )
    
    # Additional services can be registered here as they're implemented
    # For example:
    # - Cache service
    # - Metrics collector
    # - Validators
    # etc.
    
    return registry

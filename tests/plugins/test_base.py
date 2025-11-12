"""Tests for Plugin Base Interface"""

import pytest
from abc import ABC

from mcp_remote_exec.plugins.base import BasePlugin


class TestBasePlugin:
    """Tests for BasePlugin abstract class"""

    def test_cannot_instantiate_base_plugin(self):
        """Test that BasePlugin cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BasePlugin()  # type: ignore

    def test_is_abstract_base_class(self):
        """Test that BasePlugin is an ABC"""
        assert issubclass(BasePlugin, ABC)

    def test_missing_name_property(self):
        """Test that subclass must implement name property"""

        class IncompletePlugin(BasePlugin):
            def is_enabled(self, container):
                return True

            def register_tools(self, mcp, container):
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompletePlugin()

    def test_missing_is_enabled_method(self):
        """Test that subclass must implement is_enabled method"""

        class IncompletePlugin(BasePlugin):
            @property
            def name(self):
                return "incomplete"

            def register_tools(self, mcp, container):
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompletePlugin()

    def test_missing_register_tools_method(self):
        """Test that subclass must implement register_tools method"""

        class IncompletePlugin(BasePlugin):
            @property
            def name(self):
                return "incomplete"

            def is_enabled(self, container):
                return True

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompletePlugin()

    def test_complete_implementation(self):
        """Test that complete implementation can be instantiated"""

        class CompletePlugin(BasePlugin):
            @property
            def name(self):
                return "complete"

            def is_enabled(self, container):
                return True

            def register_tools(self, mcp, container):
                pass

        # Should not raise
        plugin = CompletePlugin()
        assert plugin.name == "complete"
        assert plugin.is_enabled(None) is True  # type: ignore

    def test_plugin_with_config_caching(self):
        """Test plugin that caches config (Pattern 1)"""

        class ConfigCachingPlugin(BasePlugin):
            def __init__(self):
                self._config = None

            @property
            def name(self):
                return "caching"

            def is_enabled(self, container):
                # Simulate caching config
                self._config = {"api_key": "test123"}
                return self._config is not None

            def register_tools(self, mcp, container):
                # Reuse cached config
                assert self._config is not None

        plugin = ConfigCachingPlugin()
        assert plugin.name == "caching"
        assert plugin.is_enabled(None) is True  # type: ignore
        assert plugin._config == {"api_key": "test123"}

    def test_plugin_without_config_caching(self):
        """Test plugin without config caching (Pattern 2)"""

        class NoConfigPlugin(BasePlugin):
            @property
            def name(self):
                return "noconfig"

            def is_enabled(self, container):
                # Just validate, don't cache
                return True

            def register_tools(self, mcp, container):
                # Uses services from container
                pass

        plugin = NoConfigPlugin()
        assert plugin.name == "noconfig"
        assert plugin.is_enabled(None) is True  # type: ignore

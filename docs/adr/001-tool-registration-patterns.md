# ADR 001: Tool Registration Patterns

**Status:** Accepted
**Date:** 2025-01-12
**Deciders:** Development Team

## Context

The application provides MCP tools through two different mechanisms:

1. **Core tools**: Registered via direct `@mcp.tool` decoration at module level
2. **Plugin tools**: Registered via `register_*_tools()` functions called conditionally

This difference in patterns might appear inconsistent but serves important architectural purposes.

## Decision

We use two distinct tool registration patterns:

### Pattern 1: Direct Decoration (Core Tools)

**Used for:** Essential, always-available tools that are part of core functionality

**Implementation:**

```python
# presentation/mcp_tools.py
mcp = FastMCP("mcp_remote_exec")

@mcp.tool(name="ssh_exec_command")
async def ssh_exec_command(...):
    container = bootstrap.get_container()
    return container.command_service.execute_command(...)

# bootstrap.py
def _register_ssh_file_transfer_tools(mcp_server: FastMCP) -> None:
    @mcp_server.tool(name="ssh_upload_file")
    async def ssh_upload_file(...):
        container = get_container()
        return container.file_service.upload_file(...)
```

**Characteristics:**

- Tools are decorated at module level or within private functions
- Registration happens during module import or bootstrap initialization
- Tools are always registered (or conditionally via explicit if/else logic)
- Direct access to global `mcp` instance or passed `mcp_server` parameter

### Pattern 2: Registration Functions (Plugin Tools)

**Used for:** Optional, plugin-provided tools that may or may not be available

**Implementation:**

```python
# plugins/proxmox/tools.py
def register_proxmox_tools(mcp: FastMCP, container: ServiceContainer) -> None:
    proxmox_service = container.plugin_services.get("proxmox")

    @mcp.tool(name="proxmox_container_exec_command")
    async def proxmox_container_exec_command(...):
        return proxmox_service.exec_in_container(...)
```

**Characteristics:**

- Tools are encapsulated in `register_*` functions
- Registration is called conditionally based on plugin enablement
- Allows dependency injection (container, mcp instance)
- Enables cross-plugin coordination (checking `container.enabled_plugins`)

## Rationale

### Why Direct Decoration for Core Tools?

1. **Simplicity**: Core tools are always needed, no conditional logic required
2. **Clarity**: Tool definitions are immediately visible at module level
3. **FastMCP convention**: Matches FastMCP's recommended pattern for simple servers
4. **Minimal boilerplate**: No need for extra registration functions

### Why Registration Functions for Plugins?

1. **Conditional registration**: Plugins may be disabled via environment configuration
2. **Dependency injection**: Plugins need access to their services stored in the container
3. **Cross-plugin coordination**: Plugins can check what other plugins are enabled
   - Example: Proxmox skips file transfer tools when ImageKit is enabled
4. **Separation of concerns**: Plugin tools are isolated from core registration logic
5. **Testability**: Registration functions can be tested independently
6. **Extensibility**: New plugins can be added without modifying core code

### Conditional Core Tools

Core file transfer tools (`ssh_upload_file`, `ssh_download_file`) use a hybrid approach:

- Defined in a private function `_register_ssh_file_transfer_tools()`
- Called conditionally based on ImageKit plugin status
- This bridges the gap between static and dynamic registration

```python
# bootstrap.py
imagekit_enabled = "imagekit" in _app_context.enabled_plugins
if imagekit_enabled:
    _log.warning("SSH file transfer tools NOT registered - ImageKit plugin is active")
else:
    _register_ssh_file_transfer_tools(mcp_server)
```

## Consequences

### Positive

1. **Clear separation**: Core vs plugin tools have distinct registration patterns
2. **Flexibility**: Plugins can coordinate and make decisions about tool registration
3. **Maintainability**: Each pattern is optimized for its use case
4. **Extensibility**: Adding new plugins doesn't require core code changes

### Negative

1. **Pattern asymmetry**: Developers must understand two different patterns
2. **Initial confusion**: May appear inconsistent to new contributors
3. **Documentation burden**: Requires clear documentation (this ADR)

### Mitigations

1. **Documentation**: This ADR explains the rationale
2. **Code comments**: Each pattern is clearly commented
3. **Plugin template**: BasePlugin provides clear examples in its docstring
4. **Consistent within category**: All core tools use one pattern, all plugin tools use another

## Alternatives Considered

### Alternative 1: Use Registration Functions for Everything

**Approach:** Make all tools (core and plugin) use `register_*()` functions

**Rejected because:**

- Adds unnecessary complexity for core tools
- Requires boilerplate for simple, always-on tools
- Goes against FastMCP's recommended simple patterns
- No benefit for static, non-conditional tools

### Alternative 2: Use Direct Decoration for Everything

**Approach:** Have plugins register tools at module level with conditional decorators

**Rejected because:**

- Makes cross-plugin coordination difficult
- Harder to inject dependencies (services, container)
- Conditional logic scattered across modules
- Plugin registration order matters (harder to manage)
- Testing becomes more complex

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [BasePlugin Docstring](../../src/mcp_remote_exec/plugins/base.py)
- [Plugin Registry Implementation](../../src/mcp_remote_exec/plugins/registry.py)
- [Bootstrap Module](../../src/mcp_remote_exec/presentation/bootstrap.py)

## Review

This ADR should be reviewed if:

- A third tool registration pattern is proposed
- Plugin architecture changes significantly
- FastMCP framework introduces new registration mechanisms
- Cross-plugin coordination requirements change

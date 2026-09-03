"""
agent.tools.builtin
===================
The default toolset that gives the agent real-world capabilities:

- ``run_shell``            – execute a shell command (dangerous)
- ``read_file``           – read a text file
- ``write_file``          – write/overwrite a text file (dangerous)
- ``list_directory``      – list a directory
- ``system_info``         – CPU / memory / disk snapshot
- ``os_control``          – control the OS via keyboard & mouse (dangerous)

Dangerous tools are only executed after the registry's confirmation callback
approves them, so full OS control always runs with the user's permission.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from agent.tools.base import ToolRegistry, ToolResult, tool


@tool(
    description="Execute a shell command on the host OS and return its stdout/stderr.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to run."},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)."},
        },
        "required": ["command"],
    },
    dangerous=True,
)
def run_shell(command: str, timeout: int = 60) -> ToolResult:
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(f"Command timed out after {timeout}s.", ok=False)
    out = completed.stdout or ""
    err = completed.stderr or ""
    body = out
    if err:
        body += ("\n" if body else "") + f"[stderr]\n{err}"
    body += f"\n[exit code: {completed.returncode}]"
    return ToolResult(body.strip(), ok=completed.returncode == 0)


@tool(
    description="Read and return the contents of a text file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."},
            "max_bytes": {"type": "integer", "description": "Max bytes to read (default 100000)."},
        },
        "required": ["path"],
    },
)
def read_file(path: str, max_bytes: int = 100_000) -> ToolResult:
    if not os.path.exists(path):
        return ToolResult(f"File not found: {path}", ok=False)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        data = fh.read(max_bytes)
    return ToolResult(data)


@tool(
    description="Write text to a file, creating or overwriting it.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."},
            "content": {"type": "string", "description": "Text content to write."},
        },
        "required": ["path", "content"],
    },
    dangerous=True,
)
def write_file(path: str, content: str) -> ToolResult:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return ToolResult(f"Wrote {len(content)} characters to {path}.")


@tool(
    description="List the entries of a directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (default current directory)."},
        },
    },
)
def list_directory(path: str = ".") -> ToolResult:
    if not os.path.isdir(path):
        return ToolResult(f"Not a directory: {path}", ok=False)
    entries = sorted(os.listdir(path))
    labeled = [
        f"{name}/" if os.path.isdir(os.path.join(path, name)) else name
        for name in entries
    ]
    return ToolResult("\n".join(labeled) or "(empty)")


@tool(
    description="Return a snapshot of system resource usage (CPU, memory, disk).",
    parameters={"type": "object", "properties": {}},
)
def system_info() -> ToolResult:
    try:
        import psutil
    except ImportError:
        return ToolResult("psutil is not installed; cannot read system info.", ok=False)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    lines = [
        f"CPU usage: {psutil.cpu_percent(interval=0.5)}%",
        f"CPU cores: {psutil.cpu_count(logical=True)}",
        f"Memory: {mem.percent}% used ({mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB)",
        f"Disk (/): {disk.percent}% used ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)",
    ]
    return ToolResult("\n".join(lines))


_VALID_OS_ACTIONS = {"type", "press", "hotkey", "move", "click", "scroll"}


@tool(
    name="os_control",
    description=(
        "Control the operating system through keyboard and mouse. "
        "Actions: 'type' (text), 'press' (single key), 'hotkey' (key combo, "
        "space-separated in `keys`), 'move' (mouse to x,y), 'click' (mouse "
        "button), 'scroll' (amount). Requires explicit user permission."
    ),
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": sorted(_VALID_OS_ACTIONS),
                "description": "The OS control action to perform.",
            },
            "text": {"type": "string", "description": "Text to type (action=type)."},
            "key": {"type": "string", "description": "Key to press (action=press)."},
            "keys": {"type": "string", "description": "Space-separated keys for a hotkey combo (action=hotkey)."},
            "x": {"type": "integer", "description": "Mouse X coordinate (action=move)."},
            "y": {"type": "integer", "description": "Mouse Y coordinate (action=move)."},
            "button": {"type": "string", "description": "Mouse button: left/right/middle (action=click)."},
            "amount": {"type": "integer", "description": "Scroll amount, positive=up (action=scroll)."},
        },
        "required": ["action"],
    },
    dangerous=True,
)
def os_control(
    action: str,
    text: Optional[str] = None,
    key: Optional[str] = None,
    keys: Optional[str] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    button: str = "left",
    amount: int = 0,
) -> ToolResult:
    if action not in _VALID_OS_ACTIONS:
        return ToolResult(
            f"Unknown action '{action}'. Valid: {', '.join(sorted(_VALID_OS_ACTIONS))}.",
            ok=False,
        )
    try:
        from modules.keyboard_mouse_control import control_input
    except Exception as exc:  # pyautogui/display may be unavailable
        return ToolResult(
            f"OS control unavailable: {exc}. A graphical environment and "
            "pyautogui are required.",
            ok=False,
        )

    controller = control_input()
    if action == "type":
        controller.type_text(text or "")
        return ToolResult(f"Typed {len(text or '')} characters.")
    if action == "press":
        if not key:
            return ToolResult("action=press requires 'key'.", ok=False)
        controller.press_key(key)
        return ToolResult(f"Pressed key '{key}'.")
    if action == "hotkey":
        combo = (keys or "").split()
        if not combo:
            return ToolResult("action=hotkey requires 'keys'.", ok=False)
        controller.shortcut(*combo)
        return ToolResult(f"Pressed hotkey '{'+'.join(combo)}'.")
    if action == "move":
        if x is None or y is None:
            return ToolResult("action=move requires 'x' and 'y'.", ok=False)
        controller.move_mouse(x, y)
        return ToolResult(f"Moved mouse to ({x}, {y}).")
    if action == "click":
        controller.click_mouse(button)
        return ToolResult(f"Clicked {button} mouse button.")
    if action == "scroll":
        controller.scroll_mouse(0, amount)
        return ToolResult(f"Scrolled by {amount}.")
    return ToolResult(f"Unhandled action '{action}'.", ok=False)


def build_default_registry(confirm=None) -> ToolRegistry:
    """Create a registry pre-loaded with the default toolset."""
    registry = ToolRegistry(confirm=confirm)
    registry.add(
        run_shell,
        read_file,
        write_file,
        list_directory,
        system_info,
        os_control,
    )
    return registry

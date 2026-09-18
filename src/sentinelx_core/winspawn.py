"""Process-creation flags, so nothing we spawn flashes a window on Windows.

On Windows a console application launched from a process that has no console
of its own gets a brand-new one allocated -- and that console comes with a
VISIBLE window. When the agent runs as a service or from a pythonw-based
scheduled task it has no console, so every child briefly painted a black box
on the operator's desktop: exec, git, project_snapshot, edit, local_api. One
operator counted several flashes in a row during ordinary work.

CREATE_NO_WINDOW gives the child its own console WITHOUT a window, which is
both the fix and, as handlers/script.py already relied on, what guarantees the
child has a console at all when the agent runs as a service.

This lives in one place on purpose. The flag was already applied correctly in
script.py and nowhere else; seven other spawn sites had grown up without it,
which is exactly what happens when the knowledge lives in one handler's
comments instead of in a shared helper.
"""

from __future__ import annotations

import sys
from typing import Any

# winbase.h. Not imported from subprocess because that constant only exists on
# Windows builds, and this module is imported everywhere.
CREATE_NO_WINDOW = 0x08000000


def spawn_kwargs(**extra: Any) -> dict[str, Any]:
    """Keyword arguments for create_subprocess_exec / Popen.

    On Windows adds CREATE_NO_WINDOW, merging rather than overwriting any
    creationflags the caller already passed. Everywhere else returns the extras
    untouched, so a caller can use this unconditionally.
    """
    kwargs = dict(extra)
    if sys.platform == "win32":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
    return kwargs

"""Emergency sheet / printable HTML for selected entries."""

from __future__ import annotations

import html
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

from kdbxstudio.core.database import EntryView


def render_emergency_html(
    entries: list[EntryView],
    *,
    title: str = "KDBXStudio Emergency Sheet",
    include_passwords: bool = True,
) -> str:
    rows: list[str] = []
    for entry in entries:
        password = html.escape(entry.password) if include_passwords else "••••••••"
        tags = ", ".join(html.escape(t) for t in entry.tags) or "—"
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry.title)}</td>"
            f"<td>{html.escape(entry.username)}</td>"
            f"<td>{password}</td>"
            f"<td>{html.escape(entry.url)}</td>"
            f"<td>{html.escape(entry.group_path)}</td>"
            f"<td>{tags}</td>"
            "</tr>"
        )
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    body = "\n".join(rows) or '<tr><td colspan="6">No entries</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; color: #142; }}
    h1 {{ font-size: 20px; }}
    .meta {{ color: #456; font-size: 12px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
    th, td {{
      border: 1px solid #ccd; padding: 6px 8px;
      text-align: left; vertical-align: top;
    }}
    th {{ background: #eef5f5; }}
    .warn {{ color: #a30; font-size: 12px; margin-top: 16px; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <p class="meta">Generated {html.escape(generated)} · {len(entries)} entries</p>
  <table>
    <thead>
      <tr><th>Title</th><th>Username</th><th>Password</th><th>URL</th><th>Group</th><th>Tags</th></tr>
    </thead>
    <tbody>
      {body}
    </tbody>
  </table>
  <p class="warn">Store this sheet securely. It may contain secrets in clear text.</p>
</body>
</html>
"""


def write_emergency_html(
    path: Path | str,
    entries: list[EntryView],
    *,
    title: str = "KDBXStudio Emergency Sheet",
    include_passwords: bool = True,
) -> Path:
    """Write an emergency sheet and restrict permissions to the owner (0600)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        render_emergency_html(
            entries, title=title, include_passwords=include_passwords
        ),
        encoding="utf-8",
    )
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR)
    return target

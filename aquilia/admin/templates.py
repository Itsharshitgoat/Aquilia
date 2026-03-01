"""
AquilAdmin — Template Renderer.

Renders admin HTML pages using the aqdocx design system:
- Dark/light mode with Aquilia green accent (#22c55e / #16a34a)
- Outfit font family
- Glass morphism cards
- Responsive layout

Uses Aquilia TemplateEngine when available, falls back to
inline Python string templates for zero-dependency operation.
"""

from __future__ import annotations

import html
import json
from typing import Any, Dict, List, Optional


# ── CSS Design System (matches aqdocx exactly) ──────────────────────────────

ADMIN_CSS = """
:root {
  --bg-primary: #02040a;
  --bg-card: #09090b;
  --bg-surface: #0a0a0a;
  --bg-input: #18181b;
  --border-color: #27272a;
  --border-focus: #22c55e;
  --accent: #22c55e;
  --accent-hover: #16a34a;
  --accent-glow: rgba(34, 197, 94, 0.3);
  --text-primary: #e4e4e7;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;
  --danger: #ef4444;
  --danger-hover: #dc2626;
  --warning: #f59e0b;
  --success: #22c55e;
  --info: #3b82f6;
  --font-sans: "Outfit", ui-sans-serif, system-ui, sans-serif;
  --font-mono: 'Space Mono', 'JetBrains Mono', monospace;
}
[data-theme="light"] {
  --bg-primary: #fafafa;
  --bg-card: #ffffff;
  --bg-surface: #f4f4f5;
  --bg-input: #ffffff;
  --border-color: #e4e4e7;
  --border-focus: #16a34a;
  --accent: #16a34a;
  --accent-hover: #15803d;
  --accent-glow: rgba(22, 163, 74, 0.2);
  --text-primary: #18181b;
  --text-secondary: #52525b;
  --text-muted: #71717a;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
::selection { background: var(--accent-glow); }
a { color: var(--accent); text-decoration: none; transition: color .15s; }
a:hover { color: var(--accent-hover); }

/* Layout */
.admin-layout { display: flex; min-height: 100vh; }
.admin-sidebar {
  width: 260px; background: var(--bg-card); border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0;
  z-index: 40; transition: transform .2s;
}
.admin-main { margin-left: 260px; flex: 1; min-width: 0; }
.admin-topbar {
  height: 56px; background: var(--bg-card); border-bottom: 1px solid var(--border-color);
  display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
  position: sticky; top: 0; z-index: 30;
}
.admin-content { padding: 24px; max-width: 1400px; }

/* Sidebar */
.sidebar-brand {
  padding: 20px 24px; border-bottom: 1px solid var(--border-color);
  display: flex; align-items: center; gap: 10px;
}
.sidebar-brand h1 {
  font-size: 1.1rem; font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.sidebar-brand .badge {
  font-size: 0.65rem; padding: 2px 6px; border-radius: 4px;
  background: var(--accent-glow); color: var(--accent); font-weight: 600;
}
.sidebar-nav { flex: 1; overflow-y: auto; padding: 12px 0; }
.nav-section { padding: 8px 24px 4px; font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text-muted); font-weight: 600; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 24px;
  color: var(--text-secondary); transition: all .15s; cursor: pointer;
  font-size: 0.875rem; border-left: 3px solid transparent;
}
.nav-item:hover { color: var(--text-primary); background: var(--bg-surface); }
.nav-item.active { color: var(--accent); border-left-color: var(--accent); background: var(--accent-glow); }
.nav-item .icon { font-size: 1.1rem; width: 24px; text-align: center; }

/* Cards */
.card {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: 12px; padding: 20px; transition: border-color .15s;
}
.card:hover { border-color: var(--accent-glow); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.card-title { font-size: 1rem; font-weight: 600; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px;
  padding: 20px; display: flex; align-items: center; gap: 16px;
}
.stat-icon { font-size: 2rem; width: 48px; height: 48px; display: flex; align-items: center;
  justify-content: center; border-radius: 12px; background: var(--accent-glow); }
.stat-value { font-size: 1.75rem; font-weight: 700; line-height: 1; }
.stat-label { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }

/* Table */
.admin-table { width: 100%; border-collapse: collapse; }
.admin-table th {
  text-align: left; padding: 10px 16px; font-size: 0.75rem; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--text-muted); font-weight: 600;
  border-bottom: 1px solid var(--border-color); background: var(--bg-surface);
}
.admin-table td {
  padding: 12px 16px; border-bottom: 1px solid var(--border-color);
  font-size: 0.875rem; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.admin-table tr:hover td { background: var(--bg-surface); }
.admin-table .cell-pk { font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent); }
.admin-table .cell-bool-true { color: var(--success); }
.admin-table .cell-bool-false { color: var(--text-muted); }
.admin-table input[type="checkbox"] { accent-color: var(--accent); }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px;
  border-radius: 8px; font-size: 0.875rem; font-weight: 500; cursor: pointer;
  transition: all .15s; border: 1px solid transparent; font-family: var(--font-sans);
}
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { background: var(--bg-surface); color: var(--text-primary); border-color: var(--border-color); }
.btn-secondary:hover { border-color: var(--accent); }
.btn-danger { background: var(--danger); color: #fff; }
.btn-danger:hover { background: var(--danger-hover); }
.btn-sm { padding: 4px 10px; font-size: 0.8rem; }
.btn-ghost { background: transparent; color: var(--text-secondary); }
.btn-ghost:hover { color: var(--text-primary); background: var(--bg-surface); }

/* Forms */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 6px; color: var(--text-secondary); }
.form-input {
  width: 100%; padding: 10px 14px; border-radius: 8px; font-size: 0.875rem;
  background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border-color);
  font-family: var(--font-sans); transition: border-color .15s; outline: none;
}
.form-input:focus { border-color: var(--border-focus); box-shadow: 0 0 0 3px var(--accent-glow); }
.form-input::placeholder { color: var(--text-muted); }
textarea.form-input { min-height: 100px; resize: vertical; }
select.form-input { appearance: none; }
.form-help { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }
.form-error { font-size: 0.75rem; color: var(--danger); margin-top: 4px; }

/* Search & Filter bar */
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.search-box {
  flex: 1; min-width: 200px; display: flex; align-items: center; gap: 8px;
  background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; padding: 0 12px;
}
.search-box input { border: none; background: none; color: var(--text-primary); padding: 10px 0; outline: none; width: 100%; font-family: var(--font-sans); }

/* Pagination */
.pagination { display: flex; gap: 4px; align-items: center; justify-content: center; margin-top: 20px; }
.page-btn {
  min-width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
  border-radius: 8px; font-size: 0.85rem; cursor: pointer; transition: all .15s;
  background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-secondary);
}
.page-btn:hover { border-color: var(--accent); color: var(--accent); }
.page-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.page-btn.disabled { opacity: 0.4; pointer-events: none; }

/* Flash messages */
.flash { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 0.875rem; }
.flash-success { background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: var(--success); }
.flash-error { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: var(--danger); }
.flash-info { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--info); }

/* Audit log */
.audit-entry { padding: 12px; border-bottom: 1px solid var(--border-color); }
.audit-action { font-weight: 600; text-transform: uppercase; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; }
.audit-create { background: rgba(34, 197, 94, 0.15); color: var(--success); }
.audit-update { background: rgba(59, 130, 246, 0.15); color: var(--info); }
.audit-delete { background: rgba(239, 68, 68, 0.15); color: var(--danger); }

/* Theme toggle */
.theme-toggle { cursor: pointer; font-size: 1.2rem; padding: 4px 8px; border-radius: 6px; background: var(--bg-surface); border: 1px solid var(--border-color); }

/* Responsive */
@media (max-width: 768px) {
  .admin-sidebar { transform: translateX(-100%); }
  .admin-sidebar.open { transform: translateX(0); }
  .admin-main { margin-left: 0; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
}

/* Login page */
.login-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.login-card { width: 100%; max-width: 400px; }
.login-logo { text-align: center; margin-bottom: 32px; }
.login-logo h1 { font-size: 2rem; font-weight: 800; }
"""


# ── Base Layout ──────────────────────────────────────────────────────────────

def _base_layout(title: str, content: str, sidebar_html: str = "", topbar_html: str = "") -> str:
    """Render the base admin layout."""
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} — Aquilia Admin</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>{ADMIN_CSS}</style>
</head>
<body>
    <div class="admin-layout">
        {sidebar_html}
        <div class="admin-main">
            {topbar_html}
            <div class="admin-content">
                {content}
            </div>
        </div>
    </div>
    <script>
        // Theme toggle
        function toggleTheme() {{
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('aquilia-admin-theme', next);
        }}
        // Restore theme
        const saved = localStorage.getItem('aquilia-admin-theme');
        if (saved) document.documentElement.setAttribute('data-theme', saved);
        // Select all checkbox
        function toggleAll(source) {{
            const checkboxes = document.querySelectorAll('.row-check');
            checkboxes.forEach(cb => cb.checked = source.checked);
        }}
    </script>
</body>
</html>"""


def _sidebar(app_list: List[Dict[str, Any]], active_model: str = "") -> str:
    """Render the sidebar navigation."""
    nav_items = ""
    for app in app_list:
        nav_items += f'<div class="nav-section">{html.escape(app["app_name"])}</div>'
        for model in app["models"]:
            active_cls = "active" if model["model_name"].lower() == active_model.lower() else ""
            nav_items += f'''
                <a href="/admin/{model['url_name']}/" class="nav-item {active_cls}">
                    <span class="icon">{model.get("icon", "📋")}</span>
                    <span>{html.escape(model["name_plural"])}</span>
                </a>'''

    return f"""
    <aside class="admin-sidebar">
        <div class="sidebar-brand">
            <h1>🦅 Aquilia Admin</h1>
            <span class="badge">v1.0</span>
        </div>
        <nav class="sidebar-nav">
            <a href="/admin/" class="nav-item {'active' if not active_model else ''}">
                <span class="icon">📊</span><span>Dashboard</span>
            </a>
            <a href="/admin/audit/" class="nav-item">
                <span class="icon">📝</span><span>Audit Log</span>
            </a>
            <div style="margin-top: 8px"></div>
            {nav_items}
        </nav>
        <div style="padding: 16px 24px; border-top: 1px solid var(--border-color);">
            <a href="/admin/logout" class="btn btn-ghost" style="width:100%; justify-content:center;">
                🚪 Logout
            </a>
        </div>
    </aside>"""


def _topbar(title: str = "Dashboard", identity_name: str = "") -> str:
    """Render the top bar."""
    return f"""
    <header class="admin-topbar">
        <h2 style="font-size: 1.1rem; font-weight: 600;">{html.escape(title)}</h2>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 0.85rem; color: var(--text-secondary);">{html.escape(identity_name)}</span>
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌓</button>
        </div>
    </header>"""


# ── Page Renderers ───────────────────────────────────────────────────────────


def render_login_page(error: str = "") -> str:
    """Render the admin login page."""
    error_html = f'<div class="flash flash-error">{html.escape(error)}</div>' if error else ""

    content = f"""
    <div class="login-container">
        <div class="card login-card">
            <div class="login-logo">
                <div style="font-size: 3rem; margin-bottom: 12px;">🦅</div>
                <h1 class="gradient-text" style="background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
                    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;">
                    Aquilia Admin
                </h1>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">
                    Sign in to access the admin dashboard
                </p>
            </div>
            {error_html}
            <form method="POST" action="/admin/login">
                <div class="form-group">
                    <label class="form-label">Username</label>
                    <input type="text" name="username" class="form-input" placeholder="admin" required autofocus>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-input" placeholder="••••••••" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%; justify-content: center; margin-top: 8px;">
                    Sign In
                </button>
            </form>
        </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — Aquilia Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>{ADMIN_CSS}</style>
</head>
<body>
    {content}
    <script>
        const saved = localStorage.getItem('aquilia-admin-theme');
        if (saved) document.documentElement.setAttribute('data-theme', saved);
    </script>
</body>
</html>"""


def render_dashboard(
    app_list: List[Dict[str, Any]],
    stats: Dict[str, Any],
    identity_name: str = "Admin",
) -> str:
    """Render the admin dashboard."""
    # Stats cards
    total_models = stats.get("total_models", 0)
    model_counts = stats.get("model_counts", {})
    total_records = sum(v for v in model_counts.values() if isinstance(v, int))
    recent_actions = stats.get("recent_actions", [])

    stats_html = f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon">📦</div>
            <div>
                <div class="stat-value">{total_models}</div>
                <div class="stat-label">Registered Models</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">💾</div>
            <div>
                <div class="stat-value">{total_records}</div>
                <div class="stat-label">Total Records</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div>
                <div class="stat-value">{len(recent_actions)}</div>
                <div class="stat-label">Recent Actions</div>
            </div>
        </div>
    </div>"""

    # Model cards
    models_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;">'
    for app in app_list:
        for model in app["models"]:
            count = model_counts.get(model["model_name"], "?")
            models_html += f"""
            <a href="/admin/{model['url_name']}/" style="text-decoration: none;">
                <div class="card" style="cursor: pointer;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <span style="font-size: 1.5rem;">{model.get("icon", "📋")}</span>
                        <div>
                            <div style="font-weight: 600;">{html.escape(model["name_plural"])}</div>
                            <div style="font-size: 0.8rem; color: var(--text-muted);">{html.escape(app["app_name"])}</div>
                        </div>
                    </div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent);">{count}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">records</div>
                </div>
            </a>"""
    models_html += "</div>"

    # Recent activity
    activity_html = '<div class="card" style="margin-top: 24px;"><div class="card-header"><div class="card-title">Recent Activity</div></div>'
    if recent_actions:
        for entry in recent_actions[:5]:
            action_cls = {
                "create": "audit-create",
                "update": "audit-update",
                "delete": "audit-delete",
            }.get(entry.get("action", ""), "")
            activity_html += f"""
            <div class="audit-entry">
                <span class="audit-action {action_cls}">{html.escape(str(entry.get("action", "")))}</span>
                <span style="margin-left: 8px; font-size: 0.85rem;">
                    {html.escape(str(entry.get("username", "")))} 
                    {html.escape(str(entry.get("model_name", "")))}
                </span>
                <span style="float: right; font-size: 0.75rem; color: var(--text-muted);">
                    {html.escape(str(entry.get("timestamp", ""))[:19])}
                </span>
            </div>"""
    else:
        activity_html += '<div style="padding: 20px; text-align: center; color: var(--text-muted);">No recent activity</div>'
    activity_html += "</div>"

    content = f"""
    <h1 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 24px;">Dashboard</h1>
    {stats_html}
    <h2 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 16px;">Models</h2>
    {models_html}
    {activity_html}"""

    sidebar_html = _sidebar(app_list)
    topbar_html = _topbar("Dashboard", identity_name)
    return _base_layout("Dashboard", content, sidebar_html, topbar_html)


def render_list_view(
    data: Dict[str, Any],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    flash: str = "",
    flash_type: str = "success",
) -> str:
    """Render the model list view with table, search, filters, pagination."""
    model_name = data.get("model_name", "")
    verbose_plural = data.get("verbose_name_plural", model_name)
    rows = data.get("rows", [])
    list_display = data.get("list_display", [])
    total = data.get("total", 0)
    page = data.get("page", 1)
    total_pages = data.get("total_pages", 1)
    search = data.get("search", "")
    actions = data.get("actions", {})

    flash_html = f'<div class="flash flash-{flash_type}">{html.escape(flash)}</div>' if flash else ""

    # Search bar
    search_html = f"""
    <div class="toolbar">
        <form class="search-box" method="GET" action="/admin/{model_name.lower()}/">
            <span>🔍</span>
            <input type="text" name="q" value="{html.escape(search)}" placeholder="Search {html.escape(verbose_plural)}...">
        </form>
        <a href="/admin/{model_name.lower()}/add" class="btn btn-primary">+ Add {html.escape(data.get("verbose_name", model_name))}</a>
    </div>"""

    # Table
    table_html = '<div class="card" style="padding: 0; overflow-x: auto;"><table class="admin-table"><thead><tr>'
    table_html += '<th style="width:40px"><input type="checkbox" onchange="toggleAll(this)"></th>'
    for col in list_display:
        label = col.replace("_", " ").title()
        table_html += f'<th>{html.escape(label)}</th>'
    table_html += '<th style="width:80px">Actions</th></tr></thead><tbody>'

    for row in rows:
        pk = row.get("pk", "")
        table_html += f'<tr><td><input type="checkbox" class="row-check" value="{html.escape(str(pk))}"></td>'
        for col in list_display:
            val = row.get(col, "—")
            raw_val = row.get(f"_raw_{col}")
            css_class = ""
            if col == list_display[0] or col == "id":
                css_class = "cell-pk"
            elif isinstance(raw_val, bool):
                css_class = "cell-bool-true" if raw_val else "cell-bool-false"

            if col == list_display[0]:
                table_html += f'<td class="{css_class}"><a href="/admin/{model_name.lower()}/{pk}">{html.escape(str(val))}</a></td>'
            else:
                table_html += f'<td class="{css_class}">{html.escape(str(val))}</td>'
        table_html += f'<td><a href="/admin/{model_name.lower()}/{pk}" class="btn btn-sm btn-ghost">Edit</a></td></tr>'

    if not rows:
        table_html += f'<tr><td colspan="{len(list_display) + 2}" style="text-align:center; padding:40px; color:var(--text-muted);">No records found</td></tr>'

    table_html += "</tbody></table></div>"

    # Pagination
    pagination_html = ""
    if total_pages > 1:
        pagination_html = '<div class="pagination">'
        if page > 1:
            pagination_html += f'<a href="?page={page-1}&q={html.escape(search)}" class="page-btn">←</a>'
        else:
            pagination_html += '<span class="page-btn disabled">←</span>'

        for p in range(1, total_pages + 1):
            if abs(p - page) <= 2 or p == 1 or p == total_pages:
                active = "active" if p == page else ""
                pagination_html += f'<a href="?page={p}&q={html.escape(search)}" class="page-btn {active}">{p}</a>'
            elif abs(p - page) == 3:
                pagination_html += '<span class="page-btn disabled">…</span>'

        if page < total_pages:
            pagination_html += f'<a href="?page={page+1}&q={html.escape(search)}" class="page-btn">→</a>'
        else:
            pagination_html += '<span class="page-btn disabled">→</span>'
        pagination_html += "</div>"

    # Result count
    count_html = f'<div style="text-align: center; font-size: 0.8rem; color: var(--text-muted); margin-top: 8px;">{total} record(s) found</div>'

    content = f"""
    {flash_html}
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h1 style="font-size: 1.5rem; font-weight: 700;">{html.escape(verbose_plural)}</h1>
    </div>
    {search_html}
    {table_html}
    {pagination_html}
    {count_html}"""

    sidebar_html = _sidebar(app_list, model_name)
    topbar_html = _topbar(verbose_plural, identity_name)
    return _base_layout(verbose_plural, content, sidebar_html, topbar_html)


def render_form_view(
    data: Dict[str, Any],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    is_create: bool = False,
    flash: str = "",
    flash_type: str = "success",
) -> str:
    """Render the add/edit form view."""
    model_name = data.get("model_name", "")
    verbose_name = data.get("verbose_name", model_name)
    fields = data.get("fields", [])
    fieldsets = data.get("fieldsets", [])
    pk = data.get("pk", "")
    can_delete = data.get("can_delete", False) and not is_create

    title = f"Add {verbose_name}" if is_create else f"Edit {verbose_name} #{pk}"
    action_url = f"/admin/{model_name.lower()}/add" if is_create else f"/admin/{model_name.lower()}/{pk}"

    flash_html = f'<div class="flash flash-{flash_type}">{html.escape(flash)}</div>' if flash else ""

    # Build form fields
    fields_html = ""
    for fld in fields:
        name = fld.get("name", "")
        label = fld.get("label", name)
        field_type = fld.get("type", "text")
        value = fld.get("value", "")
        required = fld.get("required", False)
        readonly = fld.get("readonly", False)
        help_text = fld.get("help_text", "")
        choices = fld.get("choices")

        if value is None:
            value = ""

        req_attr = "required" if required and not readonly else ""
        ro_attr = "readonly" if readonly else ""
        disabled = "disabled" if readonly else ""

        if field_type == "checkbox":
            checked = "checked" if value else ""
            fields_html += f"""
            <div class="form-group">
                <label class="form-label" style="display: flex; align-items: center; gap: 8px;">
                    <input type="hidden" name="{html.escape(name)}" value="">
                    <input type="checkbox" name="{html.escape(name)}" value="1" {checked} {disabled}
                        style="accent-color: var(--accent);">
                    {html.escape(label)}
                </label>
                {'<div class="form-help">' + html.escape(help_text) + '</div>' if help_text else ''}
            </div>"""
        elif field_type == "textarea":
            fields_html += f"""
            <div class="form-group">
                <label class="form-label">{html.escape(label)}</label>
                <textarea name="{html.escape(name)}" class="form-input" {req_attr} {ro_attr}>{html.escape(str(value))}</textarea>
                {'<div class="form-help">' + html.escape(help_text) + '</div>' if help_text else ''}
            </div>"""
        elif field_type == "select" and choices:
            options = ""
            for choice_val, choice_label in choices:
                selected = "selected" if str(choice_val) == str(value) else ""
                options += f'<option value="{html.escape(str(choice_val))}" {selected}>{html.escape(str(choice_label))}</option>'
            fields_html += f"""
            <div class="form-group">
                <label class="form-label">{html.escape(label)}</label>
                <select name="{html.escape(name)}" class="form-input" {req_attr} {disabled}>{options}</select>
                {'<div class="form-help">' + html.escape(help_text) + '</div>' if help_text else ''}
            </div>"""
        else:
            fields_html += f"""
            <div class="form-group">
                <label class="form-label">{html.escape(label)}</label>
                <input type="{html.escape(field_type)}" name="{html.escape(name)}" value="{html.escape(str(value))}"
                    class="form-input" {req_attr} {ro_attr}>
                {'<div class="form-help">' + html.escape(help_text) + '</div>' if help_text else ''}
            </div>"""

    # Delete button
    delete_html = ""
    if can_delete:
        delete_html = f"""
        <form method="POST" action="/admin/{model_name.lower()}/{pk}/delete"
              onsubmit="return confirm('Are you sure you want to delete this record? This cannot be undone.');"
              style="margin-top: 24px;">
            <button type="submit" class="btn btn-danger">🗑 Delete this {html.escape(verbose_name)}</button>
        </form>"""

    content = f"""
    {flash_html}
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <h1 style="font-size: 1.5rem; font-weight: 700;">{html.escape(title)}</h1>
        <a href="/admin/{model_name.lower()}/" class="btn btn-secondary">← Back to list</a>
    </div>
    <div class="card">
        <form method="POST" action="{action_url}">
            {fields_html}
            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <button type="submit" class="btn btn-primary">{'Create' if is_create else 'Save Changes'}</button>
                <a href="/admin/{model_name.lower()}/" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
    {delete_html}"""

    sidebar_html = _sidebar(app_list, model_name)
    topbar_html = _topbar(title, identity_name)
    return _base_layout(title, content, sidebar_html, topbar_html)


def render_audit_page(
    entries: List[Dict[str, Any]],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    total: int = 0,
) -> str:
    """Render the audit log page."""
    entries_html = ""
    for entry in entries:
        action = entry.get("action", "")
        action_cls = {
            "create": "audit-create",
            "update": "audit-update",
            "delete": "audit-delete",
            "login": "audit-create",
            "logout": "",
            "bulk_action": "audit-update",
        }.get(action, "")

        changes_html = ""
        changes = entry.get("changes")
        if changes and isinstance(changes, dict):
            changes_html = '<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">'
            for field_name, change in changes.items():
                if isinstance(change, dict):
                    changes_html += f'<span>{html.escape(field_name)}: {html.escape(str(change.get("old", "")))} → {html.escape(str(change.get("new", "")))}</span><br>'
                else:
                    changes_html += f'<span>{html.escape(field_name)}: {html.escape(str(change))}</span><br>'
            changes_html += '</div>'

        entries_html += f"""
        <div class="audit-entry">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="audit-action {action_cls}">{html.escape(action)}</span>
                <span style="font-weight: 500; font-size: 0.85rem;">{html.escape(str(entry.get("username", "")))}</span>
                <span style="color: var(--text-muted); font-size: 0.8rem;">on</span>
                <span style="font-size: 0.85rem;">{html.escape(str(entry.get("model_name", "") or ""))}</span>
                {f'<span style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent);">#{html.escape(str(entry.get("record_pk", "")))}</span>' if entry.get("record_pk") else ''}
                <span style="margin-left: auto; font-size: 0.75rem; color: var(--text-muted);">
                    {html.escape(str(entry.get("timestamp", ""))[:19])}
                </span>
            </div>
            {changes_html}
        </div>"""

    if not entries:
        entries_html = '<div style="padding: 40px; text-align: center; color: var(--text-muted);">No audit entries yet</div>'

    content = f"""
    <h1 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 24px;">Audit Log</h1>
    <div class="card" style="padding: 0;">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.85rem; color: var(--text-muted);">{total} entries</span>
        </div>
        {entries_html}
    </div>"""

    sidebar_html = _sidebar(app_list)
    topbar_html = _topbar("Audit Log", identity_name)
    return _base_layout("Audit Log", content, sidebar_html, topbar_html)

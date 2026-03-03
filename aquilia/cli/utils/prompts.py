"""
Aquilia CLI — Interactive prompt toolkit.

Vite-style beautiful interactive prompts built on Click.
Provides select menus, confirm toggles, multi-select, and styled
text input — all with colour-coded feedback.

Arrow-key navigation is handled via raw terminal mode (termios/tty)
so ↑↓ keys work natively without any extra dependencies.
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Optional, Sequence, Tuple

import click

from .colors import (
    _CHECK, _CROSS, _ARROW, _L_H,
)

# ═══════════════════════════════════════════════════════════════════════════
# Glyphs & colour helpers
# ═══════════════════════════════════════════════════════════════════════════

_RADIO_ON  = "●"
_RADIO_OFF = "○"
_CHECK_ON  = "◼"
_CHECK_OFF = "◻"


def _c(text: str, fg: str = "cyan", bold: bool = False, dim_: bool = False) -> str:
    return click.style(text, fg=fg, bold=bold, dim=dim_)


def _write(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


# ANSI helpers
_CLEAR_LINE  = "\033[2K"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"


def _erase_lines(n: int) -> None:
    """Erase n lines above current cursor position."""
    for _ in range(n):
        _write(f"\033[1A\033[2K")


# ═══════════════════════════════════════════════════════════════════════════
# Raw-mode key reading
# ═══════════════════════════════════════════════════════════════════════════

def _is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _read_key() -> str:
    """
    Read a single keypress in raw mode.

    Returns one of:
      'up', 'down', 'enter', 'space', 'shift_tab', 'esc', or the literal char.
    """
    import termios
    import tty

    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b":                       # ESC / arrow sequence
            ch2 = os.read(fd, 1)
            if ch2 == b"[":
                ch3 = os.read(fd, 1)
                if ch3 == b"A":
                    return "up"
                if ch3 == b"B":
                    return "down"
                if ch3 == b"Z":
                    return "shift_tab"
                return "esc"
            return "esc"
        if ch in (b"\r", b"\n"):
            return "enter"
        if ch == b" ":
            return "space"
        if ch == b"\t":
            return "tab"
        if ch == b"\x03":                       # Ctrl-C
            raise KeyboardInterrupt
        if ch == b"\x04":                       # Ctrl-D
            raise EOFError
        return ch.decode("utf-8", errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_line() -> str:
    """Read a full line in cooked mode."""
    try:
        return sys.stdin.readline().rstrip("\n")
    except (EOFError, KeyboardInterrupt):
        return ""


# ═══════════════════════════════════════════════════════════════════════════
# Flow banners
# ═══════════════════════════════════════════════════════════════════════════

def flow_header(title: str, subtitle: str = "", *, fg: str = "cyan") -> None:
    """Print a minimal flow header like Vite/create-next-app."""
    click.echo()
    click.echo(f"  {_c(title, fg=fg, bold=True)}")
    if subtitle:
        click.echo(f"  {_c(subtitle, dim_=True)}")
    click.echo()


def flow_done(message: str = "Done.", *, fg: str = "green") -> None:
    click.echo()
    click.echo(f"  {_c(_CHECK, fg=fg)} {_c(message, fg=fg, bold=True)}")
    click.echo()


# ═══════════════════════════════════════════════════════════════════════════
# Render helpers shared by select / multi_select
# ═══════════════════════════════════════════════════════════════════════════

def _render_select_rows(
    choices: Sequence[Tuple[str, str]],
    current: int,
) -> None:
    for i, (value, desc) in enumerate(choices):
        active  = i == current
        pointer = _c("❯", fg="cyan") if active else "  "
        marker  = _c(_RADIO_ON, fg="cyan") if active else _c(_RADIO_OFF, dim_=True)
        val     = _c(value, fg="cyan", bold=True) if active else _c(value, fg="white")
        d       = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
        _write(f"  {pointer} {marker} {val}{d}\n")


def _render_multi_rows(
    choices: Sequence[Tuple[str, str, bool]],
    current: int,
    selected: List[bool],
) -> None:
    for i, (value, desc, _) in enumerate(choices):
        active  = i == current
        on      = selected[i]
        pointer = _c("❯", fg="cyan") if active else "  "
        marker  = _c(_CHECK_ON, fg="green") if on else _c(_CHECK_OFF, dim_=True)
        val     = (
            _c(value, fg="cyan",  bold=True) if active else
            _c(value, fg="white", bold=True) if on     else
            _c(value, fg="white")
        )
        d = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
        _write(f"  {pointer} {marker} {val}{d}\n")


# ═══════════════════════════════════════════════════════════════════════════
# Text input
# ═══════════════════════════════════════════════════════════════════════════

def ask(
    label: str,
    *,
    default: str = "",
    required: bool = False,
    validator: Optional[Callable[[str], Optional[str]]] = None,
    hint: str = "",
) -> str:
    """Styled text input prompt with optional validation."""
    while True:
        suffix   = f" ({_c(default, fg='white', dim_=True)})" if default else ""
        hint_str = f"  {_c(hint, dim_=True)}" if hint else ""
        _write(
            f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
            f"{suffix}{hint_str} {_c('…', dim_=True)} "
        )

        value = _read_line()

        if not value and default:
            value = default

        if required and not value.strip():
            _write(f"    {_c(_CROSS, fg='red')} {_c('This field is required', fg='red')}\n")
            continue

        if validator:
            err = validator(value)
            if err:
                _write(f"    {_c(_CROSS, fg='red')} {_c(err, fg='red')}\n")
                continue

        return value


def ask_password(
    label: str,
    *,
    confirm: bool = True,
    min_length: int = 4,
) -> str:
    """Styled hidden password input with optional confirmation."""
    while True:
        prompt_text = (
            f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)} "
            f"{_c('…', dim_=True)} "
        )
        value = click.prompt(
            "", prompt_suffix="", hide_input=True, default="", show_default=False
        )
        _write(f"\033[1A\033[2K{prompt_text}{_c('*' * len(value), dim_=True)}\n")

        if len(value) < min_length:
            _write(
                f"    {_c(_CROSS, fg='red')} "
                f"{_c(f'Must be at least {min_length} characters', fg='red')}\n"
            )
            continue

        if confirm:
            confirm_text = (
                f"  {_c('◆', fg='cyan')} {_c('Confirm password', fg='white', bold=True)} "
                f"{_c('…', dim_=True)} "
            )
            confirm_val = click.prompt(
                "", prompt_suffix="", hide_input=True, default="", show_default=False
            )
            _write(
                f"\033[1A\033[2K{confirm_text}"
                f"{_c('*' * len(confirm_val), dim_=True)}\n"
            )
            if value != confirm_val:
                _write(
                    f"    {_c(_CROSS, fg='red')} "
                    f"{_c('Passwords do not match', fg='red')}\n"
                )
                continue

        return value


# ═══════════════════════════════════════════════════════════════════════════
# Select — single-choice, ↑↓ navigation
# ═══════════════════════════════════════════════════════════════════════════

def select(
    label: str,
    choices: Sequence[Tuple[str, str]],
    *,
    default: int = 0,
) -> str:
    """
    Single-choice select menu with ↑↓ arrow-key navigation.

    Falls back to numbered input when stdin is not a tty (pipes/CI).

    Args:
        label:   Prompt label
        choices: List of (value, description) tuples
        default: Initially highlighted index (0-based)

    Returns:
        Selected value string
    """
    n       = len(choices)
    current = max(0, min(default, n - 1))

    # ── Non-TTY fallback ────────────────────────────────────────────
    if not _is_tty():
        _write(f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}\n")
        for i, (value, desc) in enumerate(choices):
            mark = _c(f"{i + 1}.", dim_=True)
            v    = _c(value, fg="cyan" if i == default else "white")
            d    = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
            _write(f"    {mark} {v}{d}\n")
        while True:
            _write(f"  {_c(_ARROW, fg='cyan')} ")
            raw = _read_line().strip()
            if not raw:
                return choices[default][0]
            try:
                idx = int(raw) - 1
                if 0 <= idx < n:
                    return choices[idx][0]
            except ValueError:
                for value, _ in choices:
                    if raw.lower() == value.lower():
                        return value
            _write(f"    {_c(_CROSS, fg='red')} {_c(f'Enter 1–{n}', fg='red')}\n")

    # ── Interactive TTY mode ────────────────────────────────────────
    hint   = _c("↑↓ navigate  Enter confirm", dim_=True)
    header = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}  {hint}\n"

    _write(_HIDE_CURSOR)
    try:
        _write(header)
        _render_select_rows(choices, current)

        while True:
            key = _read_key()

            if key in ("up", "shift_tab"):
                current = (current - 1) % n
            elif key in ("down", "tab"):
                current = (current + 1) % n
            elif key == "enter":
                _erase_lines(n)
                _write(
                    f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
                    f"  {_c(choices[current][0], fg='cyan', bold=True)}\n"
                )
                return choices[current][0]
            else:
                continue

            _erase_lines(n)
            _render_select_rows(choices, current)

    except (KeyboardInterrupt, EOFError):
        _write("\n")
        raise
    finally:
        _write(_SHOW_CURSOR)


# ═══════════════════════════════════════════════════════════════════════════
# Multi-select — toggle, ↑↓ + Space
# ═══════════════════════════════════════════════════════════════════════════

def multi_select(
    label: str,
    choices: Sequence[Tuple[str, str, bool]],
) -> List[str]:
    """
    Multi-choice toggle menu with ↑↓ navigation and Space to toggle.

    Falls back to comma-separated number input when stdin is not a tty.

    Args:
        label:   Prompt label
        choices: List of (value, description, default_on) tuples

    Returns:
        List of selected value strings
    """
    n        = len(choices)
    selected = [on for _, _, on in choices]
    current  = 0

    # ── Non-TTY fallback ────────────────────────────────────────────
    if not _is_tty():
        _write(
            f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
            f"  {_c('(comma-separated numbers, Enter for defaults)', dim_=True)}\n"
        )
        for i, (value, desc, on) in enumerate(choices):
            mark = _c(_CHECK_ON if on else _CHECK_OFF,
                      fg="green" if on else "white", dim_=not on)
            num  = _c(f"{i + 1}.", dim_=True)
            v    = _c(value, fg="white", bold=on)
            d    = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
            _write(f"    {mark} {num} {v}{d}\n")
        _write(f"  {_c(_ARROW, fg='cyan')} ")
        raw = _read_line().strip()
        if not raw:
            return [v for v, _, on in choices if on]
        result: List[str] = []
        for part in raw.replace(" ", "").split(","):
            try:
                idx = int(part) - 1
                if 0 <= idx < n:
                    val = choices[idx][0]
                    if val not in result:
                        result.append(val)
            except ValueError:
                continue
        return result

    # ── Interactive TTY mode ────────────────────────────────────────
    hint   = _c("↑↓ navigate  Space toggle  Enter confirm", dim_=True)
    header = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}  {hint}\n"

    _write(_HIDE_CURSOR)
    try:
        _write(header)
        _render_multi_rows(choices, current, selected)

        while True:
            key = _read_key()

            if key in ("up", "shift_tab"):
                current = (current - 1) % n
            elif key in ("down", "tab"):
                current = (current + 1) % n
            elif key == "space":
                selected[current] = not selected[current]
            elif key == "enter":
                result_vals = [choices[i][0] for i in range(n) if selected[i]]
                summary = (
                    ", ".join(result_vals) if result_vals
                    else _c("none", dim_=True)
                )
                _erase_lines(n)
                _write(
                    f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
                    f"  {_c(summary, fg='cyan')}\n"
                )
                return result_vals
            else:
                continue

            _erase_lines(n)
            _render_multi_rows(choices, current, selected)

    except (KeyboardInterrupt, EOFError):
        _write("\n")
        raise
    finally:
        _write(_SHOW_CURSOR)


# ═══════════════════════════════════════════════════════════════════════════
# Confirm (yes/no)
# ═══════════════════════════════════════════════════════════════════════════

def confirm(
    label: str,
    *,
    default: bool = True,
) -> bool:
    """Styled yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    _write(
        f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)} "
        f"{_c(f'({hint})', dim_=True)} {_c('…', dim_=True)} "
    )
    raw = _read_line().strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1", "true")


# ═══════════════════════════════════════════════════════════════════════════
# Summary / recap table
# ═══════════════════════════════════════════════════════════════════════════

def recap(items: Sequence[Tuple[str, str]], *, title: str = "Summary") -> None:
    """Print a labelled summary of selected options."""
    click.echo()
    click.echo(
        f"  {_c(_L_H * 2, dim_=True)} "
        f"{_c(title, fg='cyan', bold=True)} "
        f"{_c(_L_H * 36, dim_=True)}"
    )
    for key, value in items:
        k       = _c(f"  {key}:", fg="white")
        v       = _c(value, fg="cyan")
        padding = " " * max(1, 20 - len(key))
        click.echo(f"  {k}{padding}{v}")
    click.echo()

# ═══════════════════════════════════════════════════════════════════════════
# Colours / glyphs
# ═══════════════════════════════════════════════════════════════════════════

_POINTER = "❯"
_RADIO_ON = "●"
_RADIO_OFF = "○"
_CHECK_ON = "◼"
_CHECK_OFF = "◻"
_GRADIENT = ["cyan", "green"]


def _c(text: str, fg: str = "cyan", bold: bool = False, dim_: bool = False) -> str:
    return click.style(text, fg=fg, bold=bold, dim=dim_)


# ═══════════════════════════════════════════════════════════════════════════
# Styled banner for interactive flows
# ═══════════════════════════════════════════════════════════════════════════

def flow_header(title: str, subtitle: str = "", *, fg: str = "cyan") -> None:
    """Print a minimal flow header like Vite/create-next-app."""
    click.echo()
    click.echo(f"  {_c(title, fg=fg, bold=True)}")
    if subtitle:
        click.echo(f"  {_c(subtitle, dim_=True)}")
    click.echo()


def flow_done(message: str = "Done.", *, fg: str = "green") -> None:
    """Print completion marker."""
    click.echo()
    click.echo(f"  {_c(_CHECK, fg=fg)} {_c(message, fg=fg, bold=True)}")
    click.echo()


# ═══════════════════════════════════════════════════════════════════════════
# Text input
# ═══════════════════════════════════════════════════════════════════════════

def ask(
    label: str,
    *,
    default: str = "",
    required: bool = False,
    validator: Optional[Callable[[str], Optional[str]]] = None,
    hint: str = "",
) -> str:
    """
    Styled text input prompt.

        ◆ Project name … my-api
    """
    while True:
        suffix = f" ({_c(default, fg='white', dim_=True)})" if default else ""
        hint_str = f"  {_c(hint, dim_=True)}" if hint else ""

        prompt_text = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}{suffix}{hint_str}"
        click.echo(prompt_text, nl=False)
        click.echo(f" {_c('…', dim_=True)} ", nl=False)

        value = click.get_text_stream("stdin").readline().rstrip("\n")

        if not value and default:
            value = default

        if required and not value.strip():
            click.echo(f"    {_c(_CROSS, fg='red')} {_c('This field is required', fg='red')}")
            continue

        if validator:
            err = validator(value)
            if err:
                click.echo(f"    {_c(_CROSS, fg='red')} {_c(err, fg='red')}")
                continue

        return value


def ask_password(
    label: str,
    *,
    confirm: bool = True,
    min_length: int = 4,
) -> str:
    """
    Styled password input (hidden).

        ◆ Password … ********
    """
    while True:
        prompt_text = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)} {_c('…', dim_=True)} "
        value = click.prompt("", prompt_suffix="", hide_input=True, default="",
                             show_default=False)
        # Re-render the line
        click.echo(f"\033[1A\033[2K{prompt_text}{_c('*' * len(value), dim_=True)}")

        if len(value) < min_length:
            click.echo(f"    {_c(_CROSS, fg='red')} {_c(f'Must be at least {min_length} characters', fg='red')}")
            continue

        if confirm:
            confirm_text = f"  {_c('◆', fg='cyan')} {_c('Confirm password', fg='white', bold=True)} {_c('…', dim_=True)} "
            confirm_val = click.prompt("", prompt_suffix="", hide_input=True,
                                        default="", show_default=False)
            click.echo(f"\033[1A\033[2K{confirm_text}{_c('*' * len(confirm_val), dim_=True)}")

            if value != confirm_val:
                click.echo(f"    {_c(_CROSS, fg='red')} {_c('Passwords do not match', fg='red')}")
                continue

        return value


# ═══════════════════════════════════════════════════════════════════════════
# Select (single choice)
# ═══════════════════════════════════════════════════════════════════════════

def select(
    label: str,
    choices: Sequence[Tuple[str, str]],
    *,
    default: int = 0,
) -> str:
    """
    Single-choice select menu (non-interactive fallback — numbered list).

        ◆ Template
          1. api         — REST API boilerplate
          2. service     — Microservice template
        → 1

    Args:
        label: Prompt label
        choices: List of (value, description) tuples
        default: Default index (0-based)

    Returns:
        Selected value string
    """
    click.echo(f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}")

    for i, (value, desc) in enumerate(choices):
        marker = _c(_RADIO_ON if i == default else _RADIO_OFF,
                     fg="cyan" if i == default else "white", dim_=i != default)
        num = _c(f"{i + 1}.", dim_=True)
        val = _c(value, fg="cyan" if i == default else "white",
                 bold=i == default)
        description = f"  {_c(_L_H, dim_=True)} {_c(desc, dim_=True)}" if desc else ""
        click.echo(f"    {marker} {num} {val}{description}")

    while True:
        prompt = f"  {_c(_ARROW, fg='cyan')} "
        click.echo(prompt, nl=False)
        raw = click.get_text_stream("stdin").readline().strip()

        if not raw:
            return choices[default][0]

        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                selected = choices[idx]
                click.echo(f"\033[1A\033[2K  {_c(_ARROW, fg='cyan')} {_c(selected[0], fg='cyan', bold=True)}")
                return selected[0]
        except ValueError:
            # Try matching by value name
            for value, desc in choices:
                if raw.lower() == value.lower():
                    return value

        click.echo(f"    {_c(_CROSS, fg='red')} {_c(f'Enter 1-{len(choices)}', fg='red')}")


# ═══════════════════════════════════════════════════════════════════════════
# Multi-select (toggle)
# ═══════════════════════════════════════════════════════════════════════════

def multi_select(
    label: str,
    choices: Sequence[Tuple[str, str, bool]],
) -> List[str]:
    """
    Multi-choice toggle menu.

        ◆ Include
          ◼ 1. Dockerfile         — Container deployment
          ◻ 2. docker-compose     — Multi-container orchestration
          ◼ 3. Makefile           — Build automation
        → 1,3 (or press Enter for defaults)

    Args:
        label: Prompt label
        choices: List of (value, description, default_on) tuples

    Returns:
        List of selected value strings
    """
    selected = [on for _, _, on in choices]

    click.echo(f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}  {_c('(comma-separated numbers, Enter for defaults)', dim_=True)}")

    for i, (value, desc, on) in enumerate(choices):
        marker = _c(_CHECK_ON if on else _CHECK_OFF,
                     fg="green" if on else "white", dim_=not on)
        num = _c(f"{i + 1}.", dim_=True)
        val = _c(value, fg="white", bold=on)
        description = f"  {_c(_L_H, dim_=True)} {_c(desc, dim_=True)}" if desc else ""
        click.echo(f"    {marker} {num} {val}{description}")

    prompt = f"  {_c(_ARROW, fg='cyan')} "
    click.echo(prompt, nl=False)
    raw = click.get_text_stream("stdin").readline().strip()

    if not raw:
        return [v for v, _, on in choices if on]

    # Parse comma-separated indices
    result = []
    for part in raw.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < len(choices):
                val = choices[idx][0]
                if val not in result:
                    result.append(val)
        except ValueError:
            continue

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Confirm (yes/no)
# ═══════════════════════════════════════════════════════════════════════════

def confirm(
    label: str,
    *,
    default: bool = True,
) -> bool:
    """
    Styled yes/no prompt.

        ◆ Include Docker files? (Y/n) …
    """
    hint = "Y/n" if default else "y/N"
    prompt_text = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)} {_c(f'({hint})', dim_=True)} {_c('…', dim_=True)} "
    click.echo(prompt_text, nl=False)
    raw = click.get_text_stream("stdin").readline().strip().lower()

    if not raw:
        return default
    return raw in ("y", "yes", "1", "true")


# ═══════════════════════════════════════════════════════════════════════════
# Summary / recap table
# ═══════════════════════════════════════════════════════════════════════════

def recap(items: Sequence[Tuple[str, str]], *, title: str = "Summary") -> None:
    """
    Print a summary of selected options.

        ── Summary ─────────────────────────────────
          Name:             my-api
          Template:         api
          Docker:           yes
    """
    click.echo()
    click.echo(f"  {_c(_L_H * 2, dim_=True)} {_c(title, fg='cyan', bold=True)} {_c(_L_H * 36, dim_=True)}")
    for key, value in items:
        k = _c(f"  {key}:", fg="white")
        v = _c(value, fg="cyan")
        padding = " " * max(1, 20 - len(key))
        click.echo(f"  {k}{padding}{v}")
    click.echo()

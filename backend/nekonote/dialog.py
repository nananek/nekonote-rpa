"""User interaction dialogs for nekonote scripts.

Usage::

    from nekonote import dialog

    dialog.show_message("Done!", title="Notice")
    ok = dialog.confirm("Continue?")
    name = dialog.input("Enter name:")
    path = dialog.open_file(filter="*.xlsx")
"""

from __future__ import annotations

import subprocess
import json
from typing import Any


def _ps_run(script: str) -> str:
    """Run a PowerShell script and return stdout."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def show_message(message: str, *, title: str = "Nekonote") -> None:
    """Show a message box."""
    _ps_run(
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'[System.Windows.Forms.MessageBox]::Show("{_escape(message)}", "{_escape(title)}")'
    )


def confirm(message: str, *, title: str = "Nekonote") -> bool:
    """Show a Yes/No dialog. Returns True if Yes."""
    result = _ps_run(
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'[System.Windows.Forms.MessageBox]::Show("{_escape(message)}", "{_escape(title)}", '
        f'"YesNo", "Question")'
    )
    return result.strip() == "Yes"


def input(message: str, *, title: str = "Nekonote", default: str = "") -> str | None:
    """Show an input dialog. Returns the entered text or None if cancelled."""
    vb_script = (
        f'$r = [Microsoft.VisualBasic.Interaction]::InputBox("{_escape(message)}", '
        f'"{_escape(title)}", "{_escape(default)}"); '
        f'if ($r -eq "") {{ "::CANCEL::" }} else {{ $r }}'
    )
    result = _ps_run(
        f'Add-Type -AssemblyName Microsoft.VisualBasic; {vb_script}'
    )
    if result == "::CANCEL::":
        return None
    return result


def select(message: str, options: list[str], *, title: str = "Nekonote") -> str | None:
    """Show a selection dialog. Returns the selected option or None."""
    opts_str = "|".join(options)
    ps = (
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'$f = New-Object System.Windows.Forms.Form; '
        f'$f.Text = "{_escape(title)}"; $f.Size = "350,250"; $f.StartPosition = "CenterScreen"; '
        f'$l = New-Object System.Windows.Forms.Label; $l.Text = "{_escape(message)}"; '
        f'$l.Location = "10,10"; $l.Size = "320,20"; $f.Controls.Add($l); '
        f'$lb = New-Object System.Windows.Forms.ListBox; $lb.Location = "10,35"; $lb.Size = "310,130"; '
        f'"{opts_str}".Split("|") | ForEach-Object {{ $lb.Items.Add($_) }}; '
        f'$f.Controls.Add($lb); '
        f'$b = New-Object System.Windows.Forms.Button; $b.Text = "OK"; $b.Location = "130,175"; '
        f'$b.Add_Click({{ $f.DialogResult = "OK"; $f.Close() }}); $f.Controls.Add($b); '
        f'$f.AcceptButton = $b; '
        f'if ($f.ShowDialog() -eq "OK" -and $lb.SelectedItem) {{ $lb.SelectedItem }} else {{ "::CANCEL::" }}'
    )
    result = _ps_run(ps)
    if result == "::CANCEL::":
        return None
    return result


def open_file(*, title: str = "Open File", filter: str = "All Files (*.*)|*.*") -> str | None:
    """Show a file open dialog. Returns the path or None."""
    result = _ps_run(
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'$d = New-Object System.Windows.Forms.OpenFileDialog; '
        f'$d.Title = "{_escape(title)}"; $d.Filter = "{_escape(filter)}"; '
        f'if ($d.ShowDialog() -eq "OK") {{ $d.FileName }} else {{ "::CANCEL::" }}'
    )
    return None if result == "::CANCEL::" else result


def save_file(*, title: str = "Save File", filter: str = "All Files (*.*)|*.*") -> str | None:
    """Show a file save dialog. Returns the path or None."""
    result = _ps_run(
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'$d = New-Object System.Windows.Forms.SaveFileDialog; '
        f'$d.Title = "{_escape(title)}"; $d.Filter = "{_escape(filter)}"; '
        f'if ($d.ShowDialog() -eq "OK") {{ $d.FileName }} else {{ "::CANCEL::" }}'
    )
    return None if result == "::CANCEL::" else result


def select_folder(*, title: str = "Select Folder") -> str | None:
    """Show a folder selection dialog. Returns the path or None."""
    result = _ps_run(
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'$d = New-Object System.Windows.Forms.FolderBrowserDialog; '
        f'$d.Description = "{_escape(title)}"; '
        f'if ($d.ShowDialog() -eq "OK") {{ $d.SelectedPath }} else {{ "::CANCEL::" }}'
    )
    return None if result == "::CANCEL::" else result


def _escape(s: str) -> str:
    """Escape for PowerShell double-quoted strings."""
    return s.replace('`', '``').replace('"', '`"').replace('$', '`$')

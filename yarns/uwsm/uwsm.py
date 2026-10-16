"""
UWSM (Universal Wayland Session Manager) Capability Yarn for Textile.
Exposes app launching and unit management via systemd user units under UWSM scope.
Layer 150 (Session Manager).
"""

import os
import shlex
import shutil
import subprocess

from needle import Yarn, strand


def _get_bin(name: str) -> str:
    resolved = shutil.which(name)
    if resolved and (resolved == name or resolved.endswith(f"/{name}")):
        return resolved
    return name


class UWSM(Yarn):
    def is_available(self) -> bool:
        return shutil.which("uwsm") is not None

    def _run_uwsm(self, action: str, target: str = "") -> str:
        uwsm_bin = _get_bin("uwsm")
        cmd = [uwsm_bin, action]
        if target:
            cmd.append(target)
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
                check=False,
            )
            return res.stdout
        except (OSError, subprocess.SubprocessError) as e:
            return f"Error running UWSM action: {e}"

    @strand.interact(capability="desktop.app_launcher")
    def launch_app(
        self,
        command: str = "",
        is_tui: bool = False,
        args: list[str] | None = None,
        app: str = "",
    ) -> str:
        """Launch a desktop application inside a dedicated systemd user scope via UWSM for clean cgroup tracking.

        :param command: The command or binary name to launch (e.g. 'firefox', 'foot', 'nvim').
        :param app: The command or binary name to launch (alias for command).
        :param is_tui: Terminal/TUI application flag (e.g. launches inside terminal with -e).
        :param args: Optional list of arguments for the application.
        """
        raw_cmd = str(command or app or "").strip()
        if not raw_cmd:
            return "Error: No command specified to launch."

        try:
            parsed_cmd = shlex.split(raw_cmd)
        except ValueError:
            parsed_cmd = [raw_cmd]

        if not parsed_cmd:
            return "Error: No command specified to launch."

        cmd_args = args or []
        if isinstance(cmd_args, str):
            cmd_args = [cmd_args]

        extra_args = [str(a) for a in cmd_args]
        uwsm_bin = _get_bin("uwsm")

        full_cmd = [uwsm_bin, "app", "-t", "service"]
        if is_tui:
            full_cmd.append("-T")
        full_cmd.extend(["--", *parsed_cmd, *extra_args])

        try:
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
                env=os.environ.copy(),
            )
            if res.returncode != 0:
                err = (
                    res.stderr.strip()
                    or res.stdout.strip()
                    or f"Exit code {res.returncode}"
                )
                return f"Error launching app via UWSM: {err}"

            mode_str = " (TUI terminal service)" if is_tui else ""
            return (
                f"Successfully launched '{raw_cmd}' via UWSM systemd service{mode_str}."
            )
        except (OSError, subprocess.SubprocessError) as e:
            return f"Error launching app via UWSM: {e}"

    @strand.observe
    def uwsm_status(self, unit: str | None = None) -> str:
        """Check UWSM Wayland session status and systemd user unit hierarchy.

        :param unit: Optional systemd unit name to query status (e.g. 'wayland-session.target').
                     Omit to check overall UWSM session status.
        """
        systemctl_bin = _get_bin("systemctl")
        uwsm_bin = _get_bin("uwsm")
        if unit and str(unit).strip():
            target_unit = str(unit).strip()
            try:
                res = subprocess.run(
                    [systemctl_bin, "--user", "status", target_unit],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=5,
                    check=False,
                )
                return res.stdout.strip()
            except (OSError, subprocess.SubprocessError) as e:
                return f"Error querying status for unit '{target_unit}': {e}"

        try:
            is_active_res = subprocess.run(
                [uwsm_bin, "check", "is-active"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
                check=False,
            )
            active_str = (
                "Active Wayland compositor session is running under UWSM."
                if is_active_res.returncode == 0
                else "No active UWSM Wayland session detected."
            )
            units_res = subprocess.run(
                [systemctl_bin, "--user", "list-units", "*uwsm*", "--no-pager"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
                check=False,
            )
            units_out = units_res.stdout.strip() or "No active UWSM systemd user units."
            return f"{active_str}\n\nUWSM Systemd User Units:\n{units_out}"
        except (OSError, subprocess.SubprocessError) as e:
            return f"Error checking UWSM status: {e}"

    @strand.observe
    def uwsm_check(self, target: str | None = None) -> str:
        """Check UWSM environment compatibility and compositor readiness.

        :param target: Check target ('is-active' or 'may-start'). Defaults to 'is-active'.
        """
        checker = (target or "is-active").strip().lower()
        if checker not in ("is-active", "may-start"):
            checker = "is-active"
        return self._run_uwsm("check", checker)

    @strand.privileged
    def uwsm_stop(self, unit: str | None = None) -> str:
        """Stop active UWSM Wayland desktop session or a specific systemd user unit.

        :param unit: Optional systemd unit or scope name to stop. Omit parameter to stop current Wayland session.
        """
        if unit and str(unit).strip():
            target_unit = str(unit).strip()
            systemctl_bin = _get_bin("systemctl")
            try:
                res = subprocess.run(
                    [systemctl_bin, "--user", "stop", target_unit],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=5,
                    check=False,
                )
                return (
                    res.stdout.strip() or f"Successfully stopped unit '{target_unit}'."
                )
            except (OSError, subprocess.SubprocessError) as e:
                return f"Error stopping unit '{target_unit}': {e}"
        return self._run_uwsm("stop")

    @strand.privileged
    def uwsm_finalize(self, target: str | None = None) -> str:
        """Finalize UWSM environment variables and session cleanup.

        :param target: Optional target for finalize.
        """
        return self._run_uwsm("finalize", target or "")

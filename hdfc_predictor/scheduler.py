"""
Scheduler & Background Automation for HDFC Bank Daily 2:00 PM Signals.
Supports macOS LaunchAgent (recommended), crontab, and background Python daemon.
"""
from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import time

from hdfc_predictor.config import settings, BASE_DIR, LOGS_DIR
from hdfc_predictor.signal_generator import SignalGenerator

LAUNCHD_LABEL = "com.user.hdfc_predictor"
LAUNCHD_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


class SchedulerManager:
    @staticmethod
    def get_python_executable() -> str:
        venv_py = BASE_DIR.parent / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)
        return sys.executable

    @classmethod
    def install_macos_launchagent(cls) -> str:
        """
        Installs a native macOS launchd plist to trigger everyday at 14:00 IST (Mon-Fri).
        Runs silently in background even if terminal is closed.
        """
        python_bin = cls.get_python_executable()
        work_dir = str(BASE_DIR.parent)
        log_out = str(LOGS_DIR / "launchd_stdout.log")
        log_err = str(LOGS_DIR / "launchd_stderr.log")

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>-m</string>
        <string>hdfc_predictor</string>
        <string>signal</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
    <key>StartCalendarInterval</key>
    <array>
        <!-- Monday through Friday at 14:00 (2:00 PM) -->
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
    </array>
    <key>StandardOutPath</key>
    <string>{log_out}</string>
    <key>StandardErrorPath</key>
    <string>{log_err}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""
        LAUNCHD_PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LAUNCHD_PLIST_PATH, "w") as f:
            f.write(plist_content)

        # Unload previous if any, then load
        try:
            subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST_PATH)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["launchctl", "load", str(LAUNCHD_PLIST_PATH)], check=True)
            return f"Successfully installed and loaded macOS LaunchAgent at {LAUNCHD_PLIST_PATH}. It will fire at 2:00 PM every weekday!"
        except Exception as e:
            return f"Wrote plist to {LAUNCHD_PLIST_PATH}, but launchctl returned: {e}"

    @classmethod
    def uninstall_macos_launchagent(cls) -> str:
        if LAUNCHD_PLIST_PATH.exists():
            subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST_PATH)], check=False)
            LAUNCHD_PLIST_PATH.unlink()
            return "macOS LaunchAgent uninstalled successfully."
        return "No active launchd service found."

    @classmethod
    def run_daemon_loop(cls):
        """
        Runs continuous in-process scheduler loop (useful for servers or docker).
        """
        import schedule
        generator = SignalGenerator()

        print("Starting HDFC Predictor Daemon. Scheduled for 14:00 IST daily.")
        schedule.every().day.at("14:00").do(generator.run_daily_signal)

        while True:
            schedule.run_pending()
            time.sleep(30)

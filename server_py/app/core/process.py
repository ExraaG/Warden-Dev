import os
import re
import sys
import time
import signal
import subprocess
import threading
from collections import deque
from typing import List, Set, Optional, Callable, Dict, Any
import psutil

class ServerProcess:
    def __init__(
        self,
        server_id: str,
        server_dir: str,
        jar_file: str,
        java_path: str = "java",
        min_memory: str = "1G",
        max_memory: str = "4G",
        jvm_args: Optional[List[str]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_status_change: Optional[Callable[[str, str], None]] = None,
    ):
        self.server_id = server_id
        self.server_dir = server_dir
        self.jar_file = jar_file
        self.java_path = java_path
        self.min_memory = min_memory
        self.max_memory = max_memory
        self.jvm_args = jvm_args or [
            "-Djava.net.preferIPv4Stack=true",
            "-Djava.net.preferIPv4Addresses=true",
            "-Dfile.encoding=UTF-8",
            "-Dterminal.jline=false",
            "-Dterminal.ansi=true",
            "--enable-native-access=ALL-UNNAMED",
            "-XX:+UseG1GC",
            "-XX:MaxGCPauseMillis=200",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+DisableExplicitGC",
        ]
        self.on_log = on_log
        self.on_status_change = on_status_change

        self.pid_file_path = os.path.join(self.server_dir, "warden.pid")
        self.status = "offline"
        self.process: Optional[subprocess.Popen] = None
        self.logs: deque = deque(maxlen=1500)
        self.online_players: Set[str] = set()
        self.start_time: float = 0.0
        self._reader_thread: Optional[threading.Thread] = None
        self._is_stopping: bool = False

    def set_status(self, new_status: str):
        if self.status != new_status:
            self.status = new_status
            if self.on_status_change:
                self.on_status_change(self.server_id, new_status)

    def add_log(self, line: str):
        cleaned = re.sub(r"(\x1b\[(0;)?\d*[A-z]?(;\d)?m?)", "", line).strip()
        if not cleaned:
            return
        self.logs.append(cleaned)
        if self.on_log:
            self.on_log(self.server_id, cleaned)

    def get_logs(self) -> List[str]:
        return list(self.logs)

    def kill_orphan_from_pid_file(self):
        if not os.path.exists(self.pid_file_path):
            return
        try:
            with open(self.pid_file_path, "r", encoding="utf-8") as f:
                pid_str = f.read().strip()
            if pid_str.isdigit():
                pid = int(pid_str)
                if psutil.pid_exists(pid):
                    p = psutil.Process(pid)
                    if "java" in p.name().lower():
                        self.add_log(f"[Warden] Found and killing orphaned Java PID {pid}...")
                        p.terminate()
                        try:
                            p.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            p.kill()
        except Exception as e:
            pass
        finally:
            self.remove_pid_file()

    def write_pid_file(self, pid: int):
        try:
            with open(self.pid_file_path, "w", encoding="utf-8") as f:
                f.write(str(pid))
        except Exception:
            pass

    def remove_pid_file(self):
        try:
            if os.path.exists(self.pid_file_path):
                os.remove(self.pid_file_path)
        except Exception:
            pass

    def _line_reader(self):
        """Crafty 4 unbuffered line reader thread reading merged stdout+stderr."""
        if not self.process or not self.process.stdout:
            return

        try:
            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                line_str = line.strip()
                if line_str:
                    self._handle_log_line(line_str)
        except Exception:
            pass
        finally:
            if self.process:
                self.process.stdout.close()
            exit_code = self.process.poll() if self.process else None
            self.add_log(f"[Warden] Process finished with exit code {exit_code}")
            if not self._is_stopping and self.status != "error":
                self.set_status("offline" if exit_code == 0 else "error")
            self.remove_pid_file()
            self._is_stopping = False

    def _handle_log_line(self, line: str):
        self.add_log(line)

        # Detect ready
        if (
            "Done (" in line
            or 'For help, type "help"' in line
            or "Ready for connections" in line
            or "Server started" in line
        ):
            if self.status != "online":
                self.set_status("online")
                self.add_log("[Warden] Minecraft server is ready and ONLINE.")

        # Detect crash
        if (
            "FAILED TO BIND TO PORT" in line
            or "Failed to initialize server" in line
            or "java.lang.OutOfMemoryError" in line
            or "Exception in server tick loop" in line
        ):
            self.set_status("error")
            self.add_log("[Warden] Fatal server crash detected. Status set to ERROR.")

        # Player join / leave tracking
        join_match = re.search(r"([a-zA-Z0-9_]{2,16})\[.*\] logged in|([a-zA-Z0-9_]{2,16}) joined the game", line, re.IGNORECASE)
        if join_match:
            player = join_match.group(1) or join_match.group(2)
            if player:
                self.online_players.add(player)

        leave_match = re.search(r"([a-zA-Z0-9_]{2,16}) lost connection|([a-zA-Z0-9_]{2,16}) left the game", line, re.IGNORECASE)
        if leave_match:
            player = leave_match.group(1) or leave_match.group(2)
            if player:
                self.online_players.discard(player)

    def start(self):
        if self.process and self.process.poll() is None:
            raise RuntimeError("Server process is already running.")

        jar_full_path = self.jar_file if os.path.isabs(self.jar_file) else os.path.join(self.server_dir, self.jar_file)
        if not os.path.exists(jar_full_path):
            raise FileNotFoundError(f"Server jar not found at {jar_full_path}")

        # Kill any orphan holding the port / directory
        self.kill_orphan_from_pid_file()

        args = [
            self.java_path,
            f"-Xms{self.min_memory}",
            f"-Xmx{self.max_memory}",
            *self.jvm_args,
            "-jar",
            jar_full_path,
            "nogui",
        ]

        self.set_status("starting")
        self.add_log(f"[Warden] Spawning Java process: {' '.join(args)}")
        self._is_stopping = False

        self.process = subprocess.Popen(
            args,
            cwd=self.server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merged streams like Crafty
            text=True,
            bufsize=1,
            env=os.environ.copy(),
        )

        if self.process.pid:
            self.write_pid_file(self.process.pid)
            self.add_log(f"[Warden] PID {self.process.pid} written to warden.pid.")

        self.start_time = time.time()
        self._reader_thread = threading.Thread(target=self._line_reader, daemon=True)
        self._reader_thread.start()

    def send_command(self, cmd: str) -> bool:
        if not self.process or self.process.poll() is not None or not self.process.stdin:
            return False
        try:
            self.add_log(f"> {cmd}")
            self.process.stdin.write(f"{cmd}\n")
            self.process.stdin.flush()
            return True
        except Exception as e:
            self.add_log(f"[Warden] Failed to send command: {e}")
            return False

    def stop(self, timeout: float = 25.0):
        if not self.process or self.process.poll() is not None:
            self.set_status("offline")
            return

        self._is_stopping = True
        self.set_status("stopping")
        self.add_log("[Warden] Sending 'stop' command to server...")

        self.send_command("stop")

        # Wait for graceful stop
        start_wait = time.time()
        while time.time() - start_wait < timeout:
            if self.process.poll() is not None:
                self.set_status("offline")
                self.remove_pid_file()
                return
            time.sleep(0.5)

        # Send SIGTERM
        if self.process.poll() is None:
            self.add_log("[Warden] Graceful stop timed out. Sending SIGTERM...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                self.set_status("offline")
                self.remove_pid_file()
                return
            except subprocess.TimeoutExpired:
                pass

        # Force SIGKILL
        if self.process.poll() is None:
            self.add_log("[Warden] SIGTERM timed out. Force killing with SIGKILL...")
            self.process.kill()
            self.set_status("offline")
            self.remove_pid_file()

    def restart(self):
        self.stop()
        time.sleep(1.5)
        self.start()

    def kill(self):
        if self.process and self.process.poll() is None:
            self.add_log("[Warden] Force killing server process...")
            self.process.kill()
            self.set_status("offline")
            self.remove_pid_file()

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "cpuPercent": 0.0,
            "memoryBytes": 0,
            "maxMemoryBytes": 0,
            "onlinePlayers": len(self.online_players),
            "maxPlayers": 20,
            "uptimeSeconds": 0,
            "status": self.status,
        }

        if self.process and self.process.poll() is None and self.process.pid:
            stats["uptimeSeconds"] = int(time.time() - self.start_time) if self.start_time else 0
            try:
                p = psutil.Process(self.process.pid)
                stats["cpuPercent"] = round(p.cpu_percent(interval=None), 1)
                mem_info = p.memory_info()
                stats["memoryBytes"] = mem_info.rss
            except Exception:
                pass

        return stats

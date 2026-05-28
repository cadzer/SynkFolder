from __future__ import annotations

import socket
import sys
import threading
from typing import Callable

HOST = "127.0.0.1"
PORT = 47651
SHOW_COMMAND = b"SHOW"
MUTEX_NAME = "SynkFolder_SingleInstance_Mutex"


class SingleInstanceGuard:
    def __init__(self) -> None:
        self._mutex_handle = None
        self._server_socket: socket.socket | None = None
        self._listener_thread: threading.Thread | None = None
        self._running = False

    def is_primary_instance(self) -> bool:
        if sys.platform == "win32":
            return self._acquire_windows_mutex()
        return self._try_bind_socket()

    def signal_existing_instance(self) -> bool:
        try:
            with socket.create_connection((HOST, PORT), timeout=2.0) as client:
                client.sendall(SHOW_COMMAND)
            return True
        except OSError:
            return False

    def start_listener(self, on_show: Callable[[], None], schedule: Callable[[Callable[[], None]], None]) -> None:
        self._running = True

        def serve() -> None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((HOST, PORT))
                sock.listen(5)
                self._server_socket = sock
                while self._running:
                    try:
                        sock.settimeout(1.0)
                        conn, _ = sock.accept()
                    except TimeoutError:
                        continue
                    except OSError:
                        break
                    with conn:
                        data = conn.recv(32)
                        if data == SHOW_COMMAND:
                            schedule(on_show)
            finally:
                sock.close()
                self._server_socket = None

        self._listener_thread = threading.Thread(target=serve, daemon=True)
        self._listener_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._server_socket is not None:
            try:
                with socket.create_connection((HOST, PORT), timeout=1.0) as wake:
                    wake.sendall(b"PING")
            except OSError:
                pass
            try:
                self._server_socket.close()
            except OSError:
                pass
        if sys.platform == "win32" and self._mutex_handle is not None:
            import ctypes

            ctypes.windll.kernel32.CloseHandle(self._mutex_handle)
            self._mutex_handle = None

    def _acquire_windows_mutex(self) -> bool:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183
        handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
        if not handle:
            return self._try_bind_socket()
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._mutex_handle = handle
        return True

    def _try_bind_socket(self) -> bool:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind((HOST, PORT))
            probe.close()
            return True
        except OSError:
            probe.close()
            return False


def ensure_single_instance() -> SingleInstanceGuard | None:
    guard = SingleInstanceGuard()
    if guard.is_primary_instance():
        return guard
    guard.signal_existing_instance()
    return None

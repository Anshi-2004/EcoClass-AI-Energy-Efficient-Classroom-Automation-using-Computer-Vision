"""
Arduino Serial Communication Module
=====================================
Handles all serial communication between Python and Arduino Uno.

Commands sent:
  '0' → AC OFF        (all LEDs off)
  '1' → AC LOW        (LED1 on,  D8)
  '2' → AC HIGH       (LED1+LED2 on, D8+D9)
  '3' → AC FULL HIGH  (LED1+LED2+LED3 on, D8+D9+D10)

Features:
  - Auto-detect available COM ports
  - Auto-reconnect on disconnect
  - Thread-safe write
  - Non-blocking background reconnect loop
"""

import serial
import serial.tools.list_ports
import threading
import time
import logging

logger = logging.getLogger(__name__)


class ArduinoController:
    """
    Manages a serial connection to an Arduino Uno and sends AC level commands.
    """

    BAUD_RATE    = 9600
    TIMEOUT      = 1          # read timeout (seconds) – not heavily used
    RECONNECT_INTERVAL = 5    # seconds between reconnect attempts

    def __init__(self, port: str = "AUTO", baud: int = BAUD_RATE):
        """
        Args:
            port: COM port string (e.g. 'COM3') or 'AUTO' to auto-detect.
            baud: Baud rate – must match Arduino sketch (default 9600).
        """
        self.port        = port
        self.baud        = baud
        self._ser: serial.Serial | None = None
        self._lock       = threading.Lock()
        self._connected  = False
        self._last_level = -1     # track last sent level to avoid redundant writes
        self._stop_event = threading.Event()

        # Start background reconnect thread
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop, daemon=True
        )
        self._reconnect_thread.start()

    # ── Public API ────────────────────────────────────────────────────────────

    def send_level(self, level: int) -> bool:
        """
        Send an AC level command to the Arduino.

        Args:
            level: 0 (OFF), 1 (LOW), 2 (HIGH), 3 (FULL HIGH).

        Returns:
            True if the command was sent successfully, False otherwise.
        """
        if level == self._last_level:
            return self._connected   # no change — skip write

        with self._lock:
            if not self._connected or self._ser is None:
                return False
            try:
                # Retry up to 3 times to ensure Arduino receives the byte
                cmd = str(level).encode()
                for attempt in range(3):
                    self._ser.write(cmd)
                    self._ser.flush()
                    time.sleep(0.05)   # 50 ms gap between retries
                self._last_level = level
                logger.info(f"Arduino ← level {level} (sent 3x)")
                return True
            except serial.SerialException as exc:
                logger.warning(f"Serial write failed: {exc}")
                self._mark_disconnected()
                return False

    def disconnect(self) -> None:
        """Cleanly close the serial port and stop the reconnect thread."""
        self._stop_event.set()
        with self._lock:
            self._close_port()

    def reconnect(self, port: str | None = None) -> bool:
        """
        Manually trigger a reconnect attempt, optionally to a new port.

        Args:
            port: New COM port string, or None to reuse self.port.

        Returns:
            True if connected successfully.
        """
        if port:
            self.port = port
        self._last_level = -1   # force re-send after reconnect
        return self._try_connect()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def active_port(self) -> str:
        """Return the currently connected port, or 'Not Connected'."""
        with self._lock:
            if self._connected and self._ser:
                return self._ser.port
        return "Not Connected"

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def list_ports() -> list[str]:
        """Return a list of available COM port names on this machine."""
        return [p.device for p in serial.tools.list_ports.comports()]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _reconnect_loop(self) -> None:
        """Background thread: keep trying to connect until stopped."""
        while not self._stop_event.is_set():
            if not self._connected:
                self._try_connect()
            time.sleep(self.RECONNECT_INTERVAL)

    def _try_connect(self) -> bool:
        """Attempt to open the serial port. Returns True on success."""
        target_port = self.port

        # Auto-detect: pick first Arduino-like port
        if target_port == "AUTO":
            candidates = self.list_ports()
            if not candidates:
                logger.debug("No COM ports found — waiting...")
                return False
            target_port = candidates[0]   # heuristic: first port

        with self._lock:
            self._close_port()
            try:
                self._ser = serial.Serial(
                    target_port,
                    self.baud,
                    timeout=self.TIMEOUT,
                )
                time.sleep(2)   # let Arduino reset after DTR toggle
                self._connected = True
                self._last_level = -1
                logger.info(f"Arduino connected on {target_port}")
                return True
            except (serial.SerialException, OSError) as exc:
                logger.debug(f"Cannot open {target_port}: {exc}")
                self._ser = None
                self._connected = False
                return False

    def _close_port(self) -> None:
        """Close serial port. Must be called while holding self._lock."""
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._connected = False

    def _mark_disconnected(self) -> None:
        """Mark as disconnected (port error). Called without lock held."""
        self._connected = False
        self._ser = None

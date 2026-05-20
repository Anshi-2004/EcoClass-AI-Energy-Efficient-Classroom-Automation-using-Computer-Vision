"""
Logic Module - Smart AC Control Logic
=======================================
This module contains all the decision-making logic:
- Determines AC level (0=OFF, 1=LOW, 2=HIGH, 3=FULL HIGH) based on student count
- Calculates suggested temperature
- Assigns room status labels
- Implements a 30-second delay to avoid flickering when room becomes empty
- Computes an energy-saving percentage indicator

AC Level thresholds:
  0 students      -> level 0 (OFF)
  1–10 students   -> level 1 (LOW)
  11–25 students  -> level 2 (HIGH)
  > 25 students   -> level 3 (FULL HIGH)
"""

import time


# ── AC level constants ────────────────────────────────────────────────────────
AC_OFF       = 0   # serial command: '0'
AC_LOW       = 1   # serial command: '1'
AC_HIGH      = 2   # serial command: '2'
AC_FULL_HIGH = 3   # serial command: '3'

AC_LEVEL_LABELS = {
    AC_OFF:       "OFF",
    AC_LOW:       "LOW",
    AC_HIGH:      "HIGH",
    AC_FULL_HIGH: "FULL HIGH",
}

AC_LEVEL_TEMPS = {
    AC_OFF:       None,
    AC_LOW:       28,
    AC_HIGH:      24,
    AC_FULL_HIGH: 20,
}


class ACController:
    """
    Smart AC controller that maps student occupancy to one of four AC levels
    and drives serial output to an Arduino Uno via LED indicators.
    """

    # Delay before turning AC OFF after room becomes empty (seconds)
    EMPTY_DELAY = 30

    # Temperature baseline for energy saving calculation
    MAX_TEMP = 28
    MIN_TEMP = 20

    def __init__(self):
        """Initialize with AC OFF state."""
        self.ac_level: int   = AC_OFF
        self.ac_on: bool     = False
        self.temperature     = None
        self.room_status: str = "Empty"
        self.message: str    = "System ready — press Start to begin."
        self.energy_saving_pct: float = 100.0

        # Empty-room delay tracking
        self._empty_since: float | None = None
        # Require this many consecutive zero-count frames before starting countdown
        # (prevents one jittery false-positive from resetting the 30s timer)
        self._ZERO_STREAK_NEEDED = 5
        self._zero_streak: int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, person_count: int) -> dict:
        """
        Update AC state based on current person count.

        Args:
            person_count: Number of students detected in the current frame.

        Returns:
            State dictionary with all dashboard fields.
        """
        now = time.time()
        empty_countdown = None

        if person_count > 0:
            # Room occupied — reset both counters
            self._zero_streak  = 0
            self._empty_since  = None
            self._apply_level(self._count_to_level(person_count), person_count)

        else:
            # Increment consecutive-zero streak
            self._zero_streak += 1

            # Only commit to "empty" after N straight zero frames
            if self._zero_streak >= self._ZERO_STREAK_NEEDED:
                if self._empty_since is None:
                    self._empty_since = now

                elapsed   = now - self._empty_since
                remaining = max(0.0, self.EMPTY_DELAY - elapsed)

                if elapsed >= self.EMPTY_DELAY:
                    # Delay expired → switch AC OFF
                    self._apply_level(AC_OFF, 0)
                    empty_countdown = 0
                else:
                    # Still in grace period — keep current level
                    empty_countdown = int(remaining)
                    self.message = (
                        f"Room appears empty — AC turns OFF in {empty_countdown}s "
                        f"if no one returns"
                    )
            else:
                # Not enough consecutive zeros yet — keep current state quietly
                self.message = "Verifying empty room..."

        return self._build_state(person_count, empty_countdown)

    def force_level(self, level: int) -> dict:
        """
        Manually override the AC level (used by dashboard buttons).

        Args:
            level: One of AC_OFF (0), AC_LOW (1), AC_HIGH (2), AC_FULL_HIGH (3).

        Returns:
            Updated state dictionary.
        """
        self._empty_since = None          # cancel any empty countdown
        self._apply_level(level, 0)      # -1 = manual override marker
        return self._build_state(0, None)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _count_to_level(count: int) -> int:
        """Map student count to AC level integer."""
        if count == 0:
            return AC_OFF
        elif count <= 10:
            return AC_LOW
        elif count <= 25:
            return AC_HIGH
        else:
            return AC_FULL_HIGH

    def _apply_level(self, level: int, count: int) -> None:
        """Apply a given AC level, updating all state fields."""
        self.ac_level   = level
        self.ac_on      = (level != AC_OFF)
        self.temperature = AC_LEVEL_TEMPS[level]
        label           = AC_LEVEL_LABELS[level]

        # Room status label
        if level == AC_OFF:
            self.room_status = "Empty"
        elif level == AC_LOW:
            self.room_status = "Low Occupancy"
        elif level == AC_HIGH:
            self.room_status = "Moderate"
        else:
            self.room_status = "High Occupancy"

        # Human-readable message
        if count == -1:
            self.message = f"⚙️ Manual override → AC {label}"
        elif level == AC_OFF:
            self.message = "Room is empty — AC turned OFF 🔋"
        else:
            temp_str = f"{self.temperature}°C" if self.temperature else "--"
            self.message = (
                f"AC {label} @ {temp_str} — "
                f"{count} student{'s' if count != 1 else ''} detected"
            )

        # Energy saving (higher temp = more saving)
        if self.temperature:
            self.energy_saving_pct = round(
                (self.temperature - self.MIN_TEMP)
                / (self.MAX_TEMP - self.MIN_TEMP) * 100,
                1,
            )
        else:
            self.energy_saving_pct = 100.0

    def _build_state(self, person_count: int, empty_countdown) -> dict:
        """Assemble and return the full state dictionary."""
        return {
            "ac_on":             self.ac_on,
            "ac_level":          self.ac_level,
            "ac_label":          AC_LEVEL_LABELS[self.ac_level],
            "temperature":       self.temperature,
            "room_status":       self.room_status,
            "message":           self.message,
            "energy_saving_pct": self.energy_saving_pct,
            "person_count":      person_count,
            "empty_countdown":   empty_countdown,
        }

    # ── Display helpers ───────────────────────────────────────────────────────

    def get_temperature_display(self) -> str:
        return f"{self.temperature}°C" if self.temperature else "— °C"

    def get_ac_status_display(self) -> str:
        return "🟢 ON" if self.ac_on else "🔴 OFF"

/*
  AI Smart Classroom - Arduino AC Controller
  ============================================
  Receives single-byte serial commands from Python:
    '0'  →  AC OFF        (all LEDs off)
    '1'  →  AC LOW        (LED1 on  — D8)
    '2'  →  AC HIGH       (LED1+LED2 — D8, D9)
    '3'  →  AC FULL HIGH  (LED1+LED2+LED3 — D8, D9, D10)

  Wiring:
    D8  → 220Ω resistor → LED1 anode  → LED1 cathode → GND
    D9  → 220Ω resistor → LED2 anode  → LED2 cathode → GND
    D10 → 220Ω resistor → LED3 anode  → LED3 cathode → GND

  STARTUP BLINK TEST:
    On power-on, each LED blinks twice in order (D8 → D9 → D10).
    Watch which physical LED blinks to confirm your wiring.
*/

// ── Pin definitions ──────────────────────────────────────────────────────────
const int LED1 = 8;   // AC LOW indicator     (D8)
const int LED2 = 9;   // AC HIGH indicator    (D9)
const int LED3 = 10;  // AC FULL indicator    (D10)

// ── Blink helper ─────────────────────────────────────────────────────────────
void blinkPin(int pin, int times, int ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(ms);
    digitalWrite(pin, LOW);
    delay(ms);
  }
}

// ── Setup ────────────────────────────────────────────────────────────────────
void setup() {
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);

  // All LEDs off at startup
  // NOTE: LED1 (D8) is active-LOW (wired anode→5V, cathode→D8)
  //       so HIGH=OFF and LOW=ON for D8 only.
  //       LED2 (D9) and LED3 (D10) are active-HIGH (normal wiring).
  setACOff();

  Serial.begin(9600);
  Serial.println("=== Arduino AC Controller ===");
  Serial.println("Running startup LED blink test...");

  // --- Blink test: each LED blinks 2x so you can verify wiring ---
  // D8 is active-LOW: pull LOW to turn ON, HIGH to turn OFF
  Serial.println("Blinking D8 (LED1 - active-LOW)...");
  digitalWrite(LED1, LOW);  delay(300);
  digitalWrite(LED1, HIGH); delay(300);
  digitalWrite(LED1, LOW);  delay(300);
  digitalWrite(LED1, HIGH); delay(300);
  delay(400);

  Serial.println("Blinking D9 (LED2 - AC HIGH)...");
  blinkPin(LED2, 2, 300);
  delay(400);

  Serial.println("Blinking D10 (LED3 - AC FULL HIGH)...");
  blinkPin(LED3, 2, 300);
  delay(400);

  setACOff();
  Serial.println("Blink test done. All LEDs OFF.");
  Serial.println("Ready for commands (0=OFF, 1=LOW, 2=HIGH, 3=FULL)");
}

// ── Main loop ────────────────────────────────────────────────────────────────
void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    switch (cmd) {
      case '0':
        setACOff();
        Serial.println("CMD 0 → AC OFF  | D8=LOW  D9=LOW  D10=LOW");
        break;
      case '1':
        setACLow();
        Serial.println("CMD 1 → AC LOW  | D8=HIGH D9=LOW  D10=LOW");
        break;
      case '2':
        setACHigh();
        Serial.println("CMD 2 → AC HIGH | D8=HIGH D9=HIGH D10=LOW");
        break;
      case '3':
        setACFullHigh();
        Serial.println("CMD 3 → AC FULL | D8=HIGH D9=HIGH D10=HIGH");
        break;
      default:
        // Ignore whitespace / newlines
        break;
    }
  }
}

// ── AC level functions ────────────────────────────────────────────────────────

// AC OFF: all LEDs off
// LED1(D8) is active-LOW → HIGH = off
void setACOff() {
  digitalWrite(LED1, HIGH);  // D8 active-LOW: HIGH = OFF
  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);
}

// AC LOW: only LED1 (D8) on
void setACLow() {
  digitalWrite(LED1, LOW);   // D8 active-LOW: LOW = ON
  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);
}

// AC HIGH: LED1 (D8) + LED2 (D9) on
void setACHigh() {
  digitalWrite(LED1, LOW);   // D8 active-LOW: LOW = ON
  digitalWrite(LED2, HIGH);
  digitalWrite(LED3, LOW);
}

// AC FULL HIGH: all three LEDs on
void setACFullHigh() {
  digitalWrite(LED1, LOW);   // D8 active-LOW: LOW = ON
  digitalWrite(LED2, HIGH);
  digitalWrite(LED3, HIGH);
}

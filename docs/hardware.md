# Hardware Plan

## Phase 1: buy now

| Part | Purpose | Notes |
|---|---|---|
| Raspberry Pi Zero 2 W | Main computer | Wi-Fi, Python, Linux, audio and display control |
| 32–64 GB microSD card | Operating system and files | Use a reputable high-endurance card |
| Reliable 5 V 2.5 A or better power supply | Stable power | Avoid underpowered phone chargers |
| Micro-USB OTG adapter or powered hub | Connect USB devices | The Zero 2 W has one data port. A powered hub is safest for a mic and speaker. |
| Small HDMI display | Animated eyes | Prefer documented Raspberry Pi support. Target resolution is 480 × 320. |
| Mini-HDMI cable or adapter | Video connection | The Zero 2 W uses mini-HDMI, not the micro-HDMI port on a Pi 4 or Pi 5. |
| USB microphone | Voice input | USB simplifies the first build |
| Small USB speaker | Voice output | A powered speaker is easiest |
| Breadboard and jumper wires | Temporary wiring | For the talk button and LEDs |
| Push buttons, LEDs, resistors | Controls/status | See push-to-talk wiring below |

## Push-to-talk button

Wire a momentary button between **BCM GPIO 17** (physical pin 11) and **GND**. The software uses the Pi's internal pull-up, so no extra resistor is required for the first test. Change the pin with `ROBOT_PTT_PIN` in `.env` if you use a different GPIO.

On a laptop, hold **V** instead of the button.

## Phase 2: add later
- Camera module
- ESP32 or Arduino controller
- Distance, light, temperature, or touch sensors
- Custom amplifier and speaker
- Rechargeable battery system
- 3D-printed enclosure

## Purchasing rules
1. Prefer documented Raspberry Pi compatibility.
2. Avoid mains-voltage electronics.
3. Avoid Li-ion battery work until power requirements are understood.
4. Record exact part models in the project journal.

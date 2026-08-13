---
source: SEAT-RND-002 (Gemini) via David Charles — relayed 2026-08-13
capture_rule: CLAUDE.md Rule 4b — VERBATIM, do not summarise
provenance: AUTHORED by Gemini (engineering formalisation). RELAYED by David. The underlying design intent is David's.
topic: RD-5 Pieces E + F — (E) system wiring & integration · (F) Isaac Lab → ONNX → Raspberry Pi sim-to-real pipeline
note: ⚠ PIECE E INTRODUCES A MAJOR DESIGN CHANGE — the hip becomes an ACTIVELY DRIVEN 3-DOF brushless spherical joint (Ø80mm ball, 3x TYI 2807 outrunners + FOC). This supersedes the earlier "passive Ø28mm pelvic ball". Architect review in chat 2026-08-13.
---

# VERBATIM — primary source, do not summarise.

## PIECE E — System Wiring & Integration Specification

This technical specification details the mechanical and electrical integration for three core subsystems: the 3-DOF Japanese Spherical Hip Joint, the Finger Servos, and the Power Delivery Network (3S LiPo to Raspberry Pi 5 & Actuators).

### 1. Japanese Sphere Joint Integration
The Japanese 3-DOF spherical joint uses three TYI 2807 1300KV brushless outrunners mounted tangentially at 120° intervals around a central Ø80mm elastomeric ball.

Layout: Motor 1 / Motor 2 / Motor 3 (each TYI 2807, each with AS5047P Encoder) → Ø80mm TPU Spherical Ball → SPI/PWM/CAN → TRIPLE-AXIS FOC DRIVER BOARD (SimpleFOC / ODrive) → High-Speed UART/USB → RASPBERRY PI 5 (CENTRAL COMPUTE)

**Mechanical & Electrical Hardware**
- Motors: 3x TYI 2807 1300KV Brushless Outrunners with Ø25mm rubber omni-wheels attached to their shafts.
- Position Encoders: 3x AS5047P 14-bit magnetic absolute position encoders mounted behind each motor rotor, communicating via SPI directly to the FOC controller.
- Control Board: Triple-axis Field Oriented Control (FOC) board (e.g., ODrive Pro, SimpleFOC Shield, or custom STM32-based FOC driver).
- Communication Interface: Connect the FOC driver board to the Raspberry Pi 5 using High-Speed UART (TX/RX) or USB-CDC. The Pi sends target vector velocity commands [Vx, Vy, ωz] at 100Hz, and the FOC board executes local closed-loop current/position control at 10kHz.

### 2. Servo Actuation System (Hand Tendons & Auxiliary Servos)
To prevent servo electrical noise from resetting the computer, servos are electrically isolated from the Raspberry Pi logic board.

Chain: Raspberry Pi 5 (3.3V Logic) → I2C (SDA/SCL) → PCA9685 16-Ch Servo Driver (Powered by dedicated 6V UBEC) → PWM Channels 1–6 → 6x MG90S Micro Servos (3 per Hand for Tendons)

**Connection Steps**
1. Signal Distribution: Connect the Pi 5's I2C pins (`GPIO 2 / SDA` and `GPIO 3 / SCL`) to a PCA9685 16-Channel 12-bit PWM Servo Driver Board.
2. Servo Powering: Power the PCA9685 terminal block from a dedicated 6V 5A High-Efficiency UBEC / Buck Regulator (converting battery voltage down to a stable 6.0V). Do not power servos directly from the Raspberry Pi 5V rail.
3. Control Interface: Wire the 6x MG90S hand servos into PWM Channels 0–5 on the PCA9685 board.

### 3. Power Architecture: 3S LiPo to Raspberry Pi 5 & Actuators
The 3S LiPo Battery (11.1V nominal, 12.6V fully charged) acts as the single primary power source. It splits into three isolated power rails to prevent brownouts when motors draw high surge currents.

3S LiPo (11.1V) → High-Current Fuse & Power Switch (15A) → three rails:
- **Rail 1: Unregulated 11.1V Raw** → Triple FOC Driver (TYI 2807 Spherical Motors)
- **Rail 2: 5.1V 5A Buck Converter** → Raspberry Pi 5 (GPIO Pins 2/4 = 5V, 6 = GND)
- **Rail 3: 6V 5A UBEC Regulator** → PCA9685 Servo Driver (MG90S Tendon Servos)

**Wiring Implementation Details**

**1. Rail 1: Raw 11.1V Main Power (Motors & FOC Driver)**
- Connect the main battery XT60 plug directly to the motor driver power stage through a 15A inline automotive blade fuse. Brushless motors operate directly on raw 3S battery voltage for maximum efficiency and torque.

**2. Rail 2: 5.1V / 5A Regulated Power (Raspberry Pi 5)**
- Buck Converter Selection: Use a step-down DC-DC buck converter capable of 5.1V output at 5A continuous (25W). Setting the output to 5.1V prevents low-voltage warnings during sudden CPU load spikes.
- Wiring to Pi 5 Header: Connect +5.1V from the buck converter to GPIO Pin 2 or Pin 4 on the Raspberry Pi 5. Connect GND from the buck converter to GPIO Pin 6 or Pin 14.
- Software Setting: Add `max_current=5000` to `/boot/firmware/config.txt` on the Pi 5. This instructs the OS that a 5A power supply is available via GPIO, bypassing USB-PD negotiation and enabling full USB port power without thermal throttling.

**3. Rail 3: 6.0V / 5A Regulated Power (Servos & Touch ADCs)**
- Connect a second buck converter (e.g., 6V UBEC) directly to the battery line to supply clean, surge-protected power for the hand servos and sensor breakout boards.

### 4. System Summary Wiring Checklist
1. Common Ground: Tie all Ground (GND) wires together at a single point near the battery terminal to eliminate ground loops.
2. LiPo Battery Protection: Install a low-voltage alarm or BMS (Battery Management System) to sound an alert if individual 3S cell voltages drop below 3.3V.
3. Power Isolation: Keep high-current motor wiring routed at least 20mm away from I2C and SPI sensor wires to avoid electromagnetic interference (EMI).

---

## PIECE F — Isaac Lab → ONNX → Raspberry Pi 5 Sim-to-Real Pipeline

To bridge the gap between training the robot in NVIDIA Isaac Lab and running those movements on the Raspberry Pi 5, you use an inference pipeline.

In simple terms: the NVIDIA GPU does all the heavy "learning" (computing billions of trial-and-error calculations per second). Once it masters the movement, it compresses its "brain" into a lightweight file format called ONNX. You copy that ONNX file onto the Raspberry Pi 5, where a python script runs it in real-time to drive the servos and motors.

### The Complete Pipeline
NVIDIA GPU (PC / Isaac Lab): simulates 512 clones of eLo · trains neural network via PPO RL · exports policy to `elo_policy.onnx` → transfer via Wi-Fi/SSH → RASPBERRY PI 5 (Robot): loads `elo_policy.onnx` with ONNX Runtime · reads IMU (tilt/accel) + Encoders + FSR Touch Sensors · evaluates ONNX at 50Hz · outputs target angles to PCA9685 & FOC Motor Boards

### Step 1: Exporting the Neural Network from NVIDIA Isaac Lab
```python
# Executed inside your Isaac Lab training script on your NVIDIA PC
import torch

# Load your best trained PPO actor network
actor_model = runner.get_actor()
actor_model.eval()

# Dummy input matching your robot's observation space
# e.g., 18 values: [Roll, Pitch, Yaw, 3x Joint Velocities, 6x Joint Angles, 6x FSR Touch States]
dummy_observation = torch.zeros(1, 18)

# Export the trained brain to ONNX
torch.onnx.export(
    actor_model,
    dummy_observation,
    "elo_policy.onnx",
    input_names=["observations"],
    output_names=["target_joint_angles"],
    dynamic_axes={"observations": {0: "batch_size"}}
)
print("Policy successfully exported to elo_policy.onnx!")
```

### Step 2: Programming the Raspberry Pi 5 Inference Engine
```bash
pip install onnxruntime Adafruit-PCA9685 smbus2 pyserial numpy
```

```python
# Main Control Loop running on the Raspberry Pi 5
import time
import numpy as np
import onnxruntime as ort
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
import serial

# 1. Initialize Communication Interfaces
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 50Hz PWM for servos

# Serial connection to Triple FOC Board (Japanese Spherical Hip Motors)
foc_serial = serial.Serial('/dev/ttyS0', 115200, timeout=0.01)

# 2. Load the Neural Network Policy
session = ort.InferenceSession("elo_policy.onnx")

def get_robot_observations():
    """
    Read real-world sensors to create the observation vector expected by the RL model.
    """
    # Example state vector (Must match Isaac Lab Observation order exactly!):
    # [IMU Roll, IMU Pitch, IMU Yaw, 3x Hand Servos Angle, 3x Hip Motor Encoders, 6x FSR Touch Pads]
    imu_roll, imu_pitch, imu_yaw = read_imu()         # 3 floats
    hand_positions = read_servo_feedback()             # 3 floats
    hip_encoders = read_foc_encoders(foc_serial)       # 3 floats
    fsr_touch_data = read_adc_fsrs()                  # 6 floats

    obs = np.array([imu_roll, imu_pitch, imu_yaw,
                    *hand_positions, *hip_encoders,
                    *fsr_touch_data], dtype=np.float32)
    return np.expand_dims(obs, axis=0) # Reshape for ONNX batch input

# 3. Main Control Loop (50 Hz = every 20ms)
LOOP_PERIOD = 0.02

while True:
    start_time = time.time()

    # Step A: Collect physical sensor state
    obs = get_robot_observations()

    # Step B: Run ONNX Neural Network Inference
    outputs = session.run(None, {"observations": obs})
    target_angles = outputs[0][0]  # Array of calculated target motor positions

    # Step C: Send Target Angles to Motors
    # 1. Update Hand Tendon Servos (PCA9685 channels 0-2)
    for i in range(3):
        servo_pwm = angle_to_pwm(target_angles[i])
        pca.channels[i].duty_cycle = servo_pwm

    # 2. Update Japanese Sphere Joint (Send velocity/position vector via UART to FOC board)
    hip_cmd = f"V {target_angles[3]:.2f} {target_angles[4]:.2f} {target_angles[5]:.2f}\n"
    foc_serial.write(hip_cmd.encode('utf-8'))

    # Step D: Maintain timing loop
    elapsed = time.time() - start_time
    if elapsed < LOOP_PERIOD:
        time.sleep(LOOP_PERIOD - elapsed)
```

### Step 3: Reinforcing the Learning Process (Sim-to-Real Domain Randomization)
In the real world, motors have latency, battery voltage drops, floor friction changes, and 3D-printed joints have slight play. If you train the model in a "perfect" simulator, it will fail on the physical robot.

| Physical Parameter | Training Randomization Range |
|---|---|
| Mass & Ballast Center | Add ±15% noise to all link masses |
| Floor Friction Coefficient | Randomize between 0.3 and 1.2 |
| Servo Reaction Delays | Inject 20ms to 60ms latency jitter |
| Sensor Noise | Add gaussian noise to IMU & FSRs |
| External Disturbance Pushes | Apply random 5N to 15N forces |

**The Continuous Reinforcement Feedback Loop:**
1. Log Real-World Telemetry: Have the Pi 5 save real-time IMU, joint angle, and FSR touch logs to a `.csv` file during operation.
2. Identify Mismatches: If eLo wobbles unexpectedly, compare the physical CSV log against the Isaac Sim prediction graph.
3. Refine Sim Parameters: Adjust the spring stiffness or joint friction values inside Isaac Sim to match your physical log, retrain the ONNX model for 10 minutes on your NVIDIA GPU, and upload the updated `.onnx` file to the Pi 5 over Wi-Fi.

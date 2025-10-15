#include <SCServo.h>
#include <Servo.h>
#include <math.h>

// PWM Servo objects
Servo baseServo;
Servo shoulderServo;

// PWM servo pins
const int baseServoPin = 11;      // PWM pin for base servo
const int shoulderServoPin = 12; // PWM pin for shoulder servo

// Center positions for PWM servos (in degrees)
const int baseCenter = 90;
const int shoulderCenter = 90;

// PWM servo trajectory vars
unsigned long pwmStartTimes[2];
int pwmStartPositions[2];
int pwmTargets[2];
bool pwmMoving[2] = {false, false};

// Unified motion duration (ms) for both PWM and bus servos
unsigned long motionDuration = 1200;

// CPG-blended trajectory control parameters
bool cpgEnabled = false;     // Off by default
float cpgAlpha = 0.25f;      // Blend factor [0..1]

// Global speed control
float speedDegPerSec = 30.0f; // default slow and precise
const unsigned long minDurationMs = 100;
const unsigned long maxDurationMs = 10000;

// Real-time feedback control
bool realTimeFeedback = false;
unsigned long lastFeedbackTime = 0;
const unsigned long feedbackInterval = 50; // 50ms = 20Hz feedback

// Per-joint durations and last logical angles
unsigned long pwmDurations[2] = {1200, 1200};
unsigned long busDurations[5] = {1200, 1200, 1200, 1200, 1200};
float pwmAnglesDeg[2] = {0.0f, 0.0f};
float busAnglesDeg[5] = {0, 0, 0, 0, 0};

void setupPWM() {
  // Attach servos to their pins
  baseServo.attach(baseServoPin);
  shoulderServo.attach(shoulderServoPin);
  
  // Initialize to center position
  baseServo.write(baseCenter);
  shoulderServo.write(shoulderCenter);
  
  // Initialize PWM trajectory vars
  pwmStartPositions[0] = baseCenter;
  pwmStartPositions[1] = shoulderCenter;
  pwmTargets[0] = baseCenter;
  pwmTargets[1] = shoulderCenter;
  
  Serial.println("PWM servos initialized");
}

void setPWMServoPosition(int servoIndex, int angle) {
  // Constrain angle to valid range
  angle = constrain(angle, 0, 180);
  
  int pwmIndex = servoIndex - 1;
  if (pwmIndex >= 0 && pwmIndex < 2) {
    // Set up trajectory
    pwmStartPositions[pwmIndex] = (pwmIndex == 0) ? baseServo.read() : shoulderServo.read();
    pwmTargets[pwmIndex] = angle;
    pwmStartTimes[pwmIndex] = millis();
    pwmMoving[pwmIndex] = true;

    // Compute per-move duration based on logical degrees delta
    int logicalDeg = map(angle, 0, 180, -90, 90);
    float delta = fabsf((float)logicalDeg - pwmAnglesDeg[pwmIndex]);
    unsigned long dur = (unsigned long)constrain((long)(1000.0f * (delta / speedDegPerSec)), (long)minDurationMs, (long)maxDurationMs);
    if (delta == 0.0f) dur = motionDuration;
    pwmDurations[pwmIndex] = dur;
    pwmAnglesDeg[pwmIndex] = (float)logicalDeg;
    
    Serial.print("PWM Servo ");
    Serial.print(servoIndex);
    Serial.print(" moving to: ");
    Serial.println(angle);
  } else {
    Serial.print("Invalid PWM servo index: ");
    Serial.println(servoIndex);
  }
}

void centerPWMServos() {
  baseServo.write(baseCenter);
  shoulderServo.write(shoulderCenter);
  Serial.println("PWM servos centered");
}

SMS_STS st;  // SMS_STS object

// Configuration for bus servos (elbow, wrist1, wrist2, wrist3, end effector)
// Note: Servos 1 and 2 are PWM servos (base and shoulder)
const byte numBusServos = 5;  // elbow, wrist1, wrist2, wrist3, end effector
const byte busServoIDs[numBusServos] = {3, 4, 5, 6, 7};  // Unique IDs for bus servos

// Enhanced servo configuration for 300° range (-150° to +150°)
const int centerPos = 2048;
const float unitsPerDegree = 4096.0 / 300.0;  // Updated for 300° range
const int maxSpeed = 3400;
const byte acc = 50;

// Servo limits for 300° range
const int minServoPos = 0;
const int maxServoPos = 4095;
const float minAngle = -150.0f;
const float maxAngle = 150.0f;

// Trajectory vars for bus servos
unsigned long startTimes[numBusServos];
int startPositions[numBusServos];
int targets[numBusServos];
bool moving[numBusServos] = {false};


// Easing kernels
float quinticEase(float t) {
  // 10t^3 - 15t^4 + 6t^5
  float t2 = t * t;
  float t3 = t2 * t;
  float t4 = t3 * t;
  float t5 = t4 * t;
  return 10.0f * t3 - 15.0f * t4 + 6.0f * t5;
}

float cpgKernel(float t) {
  // Smooth periodic kernel in [0,1] using cosine (one half-wave)
  // 0 -> 0, 1 -> 1
  const float PI_F = 3.1415926f;
  return 0.5f * (1.0f - cosf(PI_F * t));
}

float blendedProgress(float t) {
  if (t <= 0.0f) return 0.0f;
  if (t >= 1.0f) return 1.0f;
  float q = quinticEase(t);
  if (!cpgEnabled) return q;
  float c = cpgKernel(t);
  return (1.0f - cpgAlpha) * q + cpgAlpha * c;
}


void setup() {
  Serial.begin(9600);
  Serial1.begin(1000000);
  st.pSerial = &Serial1;
  while (!Serial1) {}
  
  // Initialize PWM servos
  setupPWM();
  
  // Initialize bus servos to center and check ping
  for (byte i = 0; i < numBusServos; i++) {
    int pingResult = st.Ping(busServoIDs[i]);
    if (pingResult != -1) {
      Serial.print("Bus Servo ID ");
      Serial.print(busServoIDs[i]);
      Serial.println(" detected.");
      targets[i] = centerPos;  // Fix: Initialize to center position
      st.WritePosEx(busServoIDs[i], centerPos, maxSpeed, acc);
    } else {
      Serial.print("Bus Servo ID ");
      Serial.print(busServoIDs[i]);
      Serial.println(" not detected!");
    }
  }
}

void loop() {
   if (Serial.available() > 0) {
     String input = Serial.readStringUntil('\n');
     input.trim();
     Serial.print("Received command: '");
     Serial.print(input);
     Serial.println("'");
    if (input.startsWith("change ")) {
      input = input.substring(7);
      int spaceIndex = input.indexOf(' ');
      if (spaceIndex != -1) {
        int oldID = input.substring(0, spaceIndex).toInt();
        int newID = input.substring(spaceIndex + 1).toInt();
        if (oldID >= 0 && oldID <= 253 && newID >= 0 && newID <= 253) {
          st.unLockEprom(oldID);
          st.writeByte(oldID, SMS_STS_ID, newID);
          st.LockEprom(newID);
          Serial.print("Changed ID from ");
          Serial.print(oldID);
          Serial.print(" to ");
          Serial.println(newID);
        }
      }
    } else if (input.startsWith("dur ")) {
      long newDur = input.substring(4).toInt();
      if (newDur >= 100 && newDur <= 10000) {
        motionDuration = (unsigned long)newDur;
        Serial.print("Duration set to ");
        Serial.println(motionDuration);
      } else {
        Serial.println("Invalid duration (100..10000 ms)");
      }
    } else if (input == "cpg on") {
      cpgEnabled = true;
      Serial.println("CPG enabled");
    } else if (input == "cpg off") {
      cpgEnabled = false;
      Serial.println("CPG disabled");
    } else if (input.startsWith("cpgalpha ")) {
      float a = input.substring(9).toFloat();
      if (a < 0.0f) a = 0.0f; if (a > 1.0f) a = 1.0f;
      cpgAlpha = a;
      Serial.print("CPG alpha set to ");
      Serial.println(cpgAlpha, 2);
    } else if (input.startsWith("speed ")) {
      float s = input.substring(6).toFloat();
      if (s < 1.0f) s = 1.0f; if (s > 180.0f) s = 180.0f;
      speedDegPerSec = s;
      Serial.print("Speed set to ");
      Serial.print(speedDegPerSec, 1);
      Serial.println(" deg/s");
    } else if (input == "readall") {
       int pwm0 = map(baseServo.read(), 0, 180, -90, 90);
       int pwm1 = map(shoulderServo.read(), 0, 180, -90, 90);
       int vals[7];
       vals[0] = pwm0; vals[1] = pwm1;
       for (byte i = 0; i < numBusServos; i++) {
         int p = st.ReadPos(busServoIDs[i]);
         if (p == -1) {
           vals[i+2] = (int)busAnglesDeg[i];
         } else {
           float deg = (p - centerPos) / unitsPerDegree;
           if (deg < minAngle) deg = minAngle; if (deg > maxAngle) deg = maxAngle;
           vals[i+2] = (int)deg;
         }
       }
       Serial.print("fb ");
       for (int i=0;i<7;i++) { Serial.print(vals[i]); if (i<6) Serial.print(","); }
       Serial.println();
    } else if (input == "realtime on") {
       realTimeFeedback = true;
       Serial.println("Real-time feedback enabled");
    } else if (input == "realtime off") {
       realTimeFeedback = false;
       Serial.println("Real-time feedback disabled");
    } else if (input.startsWith("read ")) {
      int idx = input.substring(5).toInt();
      if (idx >= 1 && idx <= 7) {
        int val = 0;
        if (idx == 1) val = map(baseServo.read(), 0, 180, -90, 90);
        else if (idx == 2) val = map(shoulderServo.read(), 0, 180, -90, 90);
        else {
          int p = st.ReadPos(busServoIDs[idx-3]);
          if (p == -1) val = (int)busAnglesDeg[idx-3];
          else {
            float deg = (p - centerPos) / unitsPerDegree;
            if (deg < minAngle) deg = minAngle; if (deg > maxAngle) deg = maxAngle;
            val = (int)deg;
          }
        }
        Serial.print("fb "); Serial.print(idx); Serial.print(" "); Serial.println(val);
      }
    } else {
      int spaceIndex = input.indexOf(' ');
      if (spaceIndex != -1) {
        String idxStr = input.substring(0, spaceIndex);
        String angStr = input.substring(spaceIndex + 1);
        int index = idxStr.toInt();
        int angle = angStr.toInt();
        
        // Handle PWM servos (1 and 2)
        if (index == 1 || index == 2) {
          // Convert angle from -90~90 to 0~180 for PWM servos
          int pwmAngle = map(angle, -90, 90, 0, 180);
          setPWMServoPosition(index, pwmAngle);
        }
         // Handle bus servos (3, 4, 5, 6, 7)
         else if (index >= 3 && index <= 7 && angle >= -150 && angle <= 150) {
           // Convert index to bus servo array index
           int busIndex = index - 3;
           int newTarget = centerPos + (int)(angle * unitsPerDegree + 0.5);
           newTarget = constrain(newTarget, minServoPos, maxServoPos);

           Serial.print("Bus Servo ");
           Serial.print(index);
           Serial.print(" target: ");
           Serial.print(newTarget);
           Serial.print(" (angle: ");
           Serial.print(angle);
           Serial.println("°)");

           if (newTarget != targets[busIndex]) {
             startPositions[busIndex] = st.ReadPos(busServoIDs[busIndex]);
             // Improve error handling: If reading position fails, use the last target position
             if (startPositions[busIndex] == -1) {
               startPositions[busIndex] = targets[busIndex];
               Serial.print("Warning: Failed to read current position for servo ");
               Serial.print(index);
               Serial.println(", using last target");
             }
             startTimes[busIndex] = millis();
             targets[busIndex] = newTarget;
             moving[busIndex] = true;
             float delta = fabsf(angle - busAnglesDeg[busIndex]);
             unsigned long dur = (unsigned long)constrain((long)(1000.0f * (delta / speedDegPerSec)), (long)minDurationMs, (long)maxDurationMs);
             if (delta == 0.0f) dur = motionDuration;
             busDurations[busIndex] = dur;
             busAnglesDeg[busIndex] = (float)angle;

             Serial.print("Bus Servo ");
             Serial.print(index);
             Serial.println(" moving initiated");
           } else {
             Serial.print("Bus Servo ");
             Serial.print(index);
             Serial.println(" already at target position");
           }
         }
      }
    }
  }
  
  // Update PWM servos
  unsigned long currentTime = millis();
  for (byte i = 0; i < 2; i++) {
    if (pwmMoving[i]) {
      unsigned long elapsed = currentTime - pwmStartTimes[i];
      if (elapsed >= pwmDurations[i]) {
        if (i == 0) {
          baseServo.write(pwmTargets[i]);
        } else {
          shoulderServo.write(pwmTargets[i]);
        }
        pwmMoving[i] = false;
      } else {
        float tau = (float)elapsed / (float)pwmDurations[i];
        float relative = blendedProgress(tau);
        int pos = pwmStartPositions[i] + (int)((pwmTargets[i] - pwmStartPositions[i]) * relative);
        if (i == 0) {
          baseServo.write(pos);
        } else {
          shoulderServo.write(pos);
        }
      }
    }
  }
  
  // Update bus servos
  for (byte i = 0; i < numBusServos; i++) {
    if (moving[i]) {
      unsigned long elapsed = currentTime - startTimes[i];
      if (elapsed >= busDurations[i]) {
        st.WritePosEx(busServoIDs[i], targets[i], maxSpeed, acc);
        moving[i] = false;
      } else {
        float tau = (float)elapsed / (float)busDurations[i];
        float relative = blendedProgress(tau);
        int pos = startPositions[i] + (int)((targets[i] - startPositions[i]) * relative);
        st.WritePosEx(busServoIDs[i], pos, maxSpeed, acc);
      }
    }
  }

  // Real-time position feedback
  if (realTimeFeedback && (millis() - lastFeedbackTime >= feedbackInterval)) {
    int pwm0 = map(baseServo.read(), 0, 180, -90, 90);
    int pwm1 = map(shoulderServo.read(), 0, 180, -90, 90);
    int vals[7];
    vals[0] = pwm0; vals[1] = pwm1;

    for (byte i = 0; i < numBusServos; i++) {
      int p = st.ReadPos(busServoIDs[i]);
      if (p == -1) {
        vals[i+2] = (int)busAnglesDeg[i];
      } else {
        float deg = (p - centerPos) / unitsPerDegree;
        if (deg < minAngle) deg = minAngle; if (deg > maxAngle) deg = maxAngle;
        vals[i+2] = (int)deg;
      }
    }

    Serial.print("rt ");
    for (int i=0;i<7;i++) { Serial.print(vals[i]); if (i<6) Serial.print(","); }
    Serial.println();
    lastFeedbackTime = millis();
  }

  delay(5); // Reduced delay for faster response
}
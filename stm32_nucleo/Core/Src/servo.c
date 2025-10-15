/**
  ******************************************************************************
  * @file    servo.c
  * @brief   Servo control implementation for STM32 Nucleo G474RE
  * @description High-performance servo control with trajectory planning
  *              Supports PWM and UART bus servos with smooth motion profiles
  ******************************************************************************
  */

/* Includes ------------------------------------------------------------------*/
#include "servo.h"
#include "stm32g4xx_hal.h"
#include <string.h>
#include <math.h>

/* Private defines -----------------------------------------------------------*/
#define PWM_PULSE_MIN 500     // 0.5ms pulse (0°)
#define PWM_PULSE_MAX 2500    // 2.5ms pulse (180°)
#define PWM_PULSE_CENTER 1500 // 1.5ms pulse (90°)

/* Bus servo protocol */
#define BUS_SERVO_FRAME_HEADER 0xFF
#define BUS_SERVO_CMD_WRITE 0x03
#define BUS_SERVO_BROADCAST_ID 0xFE

/* Private variables ---------------------------------------------------------*/
extern UART_HandleTypeDef huart1;
extern TIM_HandleTypeDef htim2;

/* Private function prototypes -----------------------------------------------*/
static void Servo_PWM_SetPosition(ServoConfig_t* config, uint16_t pulseWidth);
static void Servo_Bus_SetPosition(ServoConfig_t* config, int16_t position);
static int16_t Servo_AngleToPosition(ServoConfig_t* config, float angle);
static float Servo_PositionToAngle(ServoConfig_t* config, int16_t position);
static float QuinticEase(float t);
static float CPGKernel(float t);
static float BlendedProgress(float t);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize servo system
 */
void Servo_Init(ServoConfig_t* config, ServoState_t* state, uint8_t numServos)
{
    // Initialize PWM servos (servos 1-2)
    for (int i = 0; i < PWM_SERVOS && i < numServos; i++) {
        config[i].id = i + 1;
        config[i].type = 0; // PWM servo
        config[i].htim = &htim2;
        config[i].timChannel = (i == 0) ? TIM_CHANNEL_1 : TIM_CHANNEL_2;
        config[i].centerPos = 90; // 90° center
        config[i].minPos = 0;
        config[i].maxPos = 180;
        config[i].minAngle = -90.0f;
        config[i].maxAngle = 90.0f;
        config[i].unitsPerDegree = 1.0f;

        // Initialize state
        state[i].currentAngle = 0.0f;
        state[i].targetAngle = 0.0f;
        state[i].currentPos = config[i].centerPos;
        state[i].targetPos = config[i].centerPos;
        state[i].moving = false;
    }

    // Initialize bus servos (servos 3-7)
    for (int i = PWM_SERVOS; i < numServos && i < MAX_SERVOS; i++) {
        config[i].id = i + 1;
        config[i].type = 1; // Bus servo
        config[i].channel = i - PWM_SERVOS + 3; // Bus servo IDs 3-7
        config[i].centerPos = BUS_SERVO_CENTER_POS;
        config[i].minPos = 0;
        config[i].maxPos = 4095;
        config[i].minAngle = -150.0f;
        config[i].maxAngle = 150.0f;
        config[i].unitsPerDegree = BUS_SERVO_UNITS_PER_DEGREE;

        // Initialize state
        state[i].currentAngle = 0.0f;
        state[i].targetAngle = 0.0f;
        state[i].currentPos = config[i].centerPos;
        state[i].targetPos = config[i].centerPos;
        state[i].moving = false;
    }
}

/**
 * @brief Initialize UART for bus servo communication
 */
void Servo_UART_Init(UART_HandleTypeDef* huart)
{
    // UART is already initialized in main.c via MX_USART1_UART_Init()
    // This function can be used for additional bus servo initialization if needed
}

/**
 * @brief Center all servos to their center positions
 */
void Servo_CenterAll(ServoConfig_t* config, ServoState_t* state, uint8_t numServos)
{
    for (int i = 0; i < numServos; i++) {
        Servo_SetTargetAngle(config, state, i, 0.0f, 30.0f, 1200);
    }
}

/**
 * @brief Set target angle for a servo with trajectory planning
 */
void Servo_SetTargetAngle(ServoConfig_t* config, ServoState_t* state,
                         uint8_t servoIndex, float angle, float speedDegPerSec, uint32_t durationMs)
{
    if (servoIndex >= MAX_SERVOS) return;

    // Constrain angle to valid range
    if (angle < config[servoIndex].minAngle) angle = config[servoIndex].minAngle;
    if (angle > config[servoIndex].maxAngle) angle = config[servoIndex].maxAngle;

    // Calculate duration based on angle delta if not specified
    if (durationMs == 0) {
        float delta = fabsf(angle - state[servoIndex].currentAngle);
        durationMs = (uint32_t)(1000.0f * (delta / speedDegPerSec));
        if (durationMs < 100) durationMs = 100;
        if (durationMs > 10000) durationMs = 10000;
    }

    // Set up trajectory
    state[servoIndex].currentAngle = state[servoIndex].targetAngle;
    state[servoIndex].targetAngle = angle;
    state[servoIndex].currentPos = state[servoIndex].targetPos;
    state[servoIndex].targetPos = Servo_AngleToPosition(&config[servoIndex], angle);
    state[servoIndex].startTime = HAL_GetTick();
    state[servoIndex].duration = durationMs;
    state[servoIndex].moving = true;
}

/**
 * @brief Update servo position using trajectory planning
 */
float Servo_UpdatePosition(ServoConfig_t* config, ServoState_t* state,
                          uint8_t servoIndex, uint32_t currentTime)
{
    if (servoIndex >= MAX_SERVOS || !state[servoIndex].moving) {
        return 1.0f;
    }

    uint32_t elapsed = currentTime - state[servoIndex].startTime;
    float tau = (float)elapsed / (float)state[servoIndex].duration;

    if (tau >= 1.0f) {
        // Motion completed
        state[servoIndex].currentPos = state[servoIndex].targetPos;
        state[servoIndex].currentAngle = state[servoIndex].targetAngle;
        state[servoIndex].moving = false;

        // Set final position
        if (config[servoIndex].type == 0) {
            // PWM servo
            uint16_t pulseWidth = PWM_PULSE_MIN + (state[servoIndex].currentPos * (PWM_PULSE_MAX - PWM_PULSE_MIN)) / 180;
            Servo_PWM_SetPosition(&config[servoIndex], pulseWidth);
        } else {
            // Bus servo
            Servo_Bus_SetPosition(&config[servoIndex], state[servoIndex].currentPos);
        }

        return 1.0f;
    }

    // Calculate eased progress
    float progress = BlendedProgress(tau);

    // Calculate intermediate position
    int16_t newPos = state[servoIndex].currentPos +
                    (int16_t)((state[servoIndex].targetPos - state[servoIndex].currentPos) * progress);

    // Update servo position
    if (config[servoIndex].type == 0) {
        // PWM servo
        uint16_t pulseWidth = PWM_PULSE_MIN + (newPos * (PWM_PULSE_MAX - PWM_PULSE_MIN)) / 180;
        Servo_PWM_SetPosition(&config[servoIndex], pulseWidth);
    } else {
        // Bus servo
        Servo_Bus_SetPosition(&config[servoIndex], newPos);
    }

    return tau;
}

/**
 * @brief Get current position of a servo
 */
int16_t Servo_GetPosition(ServoConfig_t* config, ServoState_t* state, uint8_t servoIndex)
{
    if (servoIndex >= MAX_SERVOS) return 0;
    return (int16_t)state[servoIndex].currentAngle;
}

/**
 * @brief Get positions of all servos
 */
void Servo_GetAllPositions(ServoConfig_t* config, ServoState_t* state,
                          int16_t* positions, uint8_t numServos)
{
    for (int i = 0; i < numServos && i < MAX_SERVOS; i++) {
        positions[i] = (int16_t)state[i].currentAngle;
    }
}

/**
 * @brief Check if a servo is currently moving
 */
bool Servo_IsMoving(ServoState_t* state, uint8_t servoIndex)
{
    if (servoIndex >= MAX_SERVOS) return false;
    return state[servoIndex].moving;
}

/**
 * @brief Stop all servo movements immediately
 */
void Servo_StopAll(ServoConfig_t* config, ServoState_t* state, uint8_t numServos)
{
    for (int i = 0; i < numServos && i < MAX_SERVOS; i++) {
        state[i].moving = false;

        // Set current position to target position
        if (config[i].type == 0) {
            // PWM servo
            uint16_t pulseWidth = PWM_PULSE_MIN + (state[i].targetPos * (PWM_PULSE_MAX - PWM_PULSE_MIN)) / 180;
            Servo_PWM_SetPosition(&config[i], pulseWidth);
        } else {
            // Bus servo
            Servo_Bus_SetPosition(&config[i], state[i].targetPos);
        }
    }
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Set PWM servo position
 */
static void Servo_PWM_SetPosition(ServoConfig_t* config, uint16_t pulseWidth)
{
    __HAL_TIM_SET_COMPARE(config->htim, config->timChannel, pulseWidth);
}

/**
 * @brief Set bus servo position
 */
static void Servo_Bus_SetPosition(ServoConfig_t* config, int16_t position)
{
    uint8_t id = config->channel;
    uint16_t pos = (uint16_t)position;
    uint16_t speed = 3400; // Max speed
    uint8_t acc = 50;      // Acceleration

    // Create bus servo command frame
    uint8_t frame[11];
    frame[0] = BUS_SERVO_FRAME_HEADER;
    frame[1] = BUS_SERVO_FRAME_HEADER;
    frame[2] = id;
    frame[3] = 7; // Data length
    frame[4] = BUS_SERVO_CMD_WRITE;
    frame[5] = 0x2A; // Position address
    frame[6] = pos & 0xFF;        // Position low byte
    frame[7] = (pos >> 8) & 0xFF; // Position high byte
    frame[8] = speed & 0xFF;      // Speed low byte
    frame[9] = (speed >> 8) & 0xFF; // Speed high byte

    // Calculate checksum
    uint8_t checksum = id + 7 + BUS_SERVO_CMD_WRITE + 0x2A + frame[6] + frame[7] + frame[8] + frame[9];
    frame[10] = ~checksum;

    // Send via UART
    HAL_UART_Transmit(&huart1, frame, sizeof(frame), HAL_MAX_DELAY);
}

/**
 * @brief Convert angle to servo position
 */
static int16_t Servo_AngleToPosition(ServoConfig_t* config, float angle)
{
    if (config->type == 0) {
        // PWM servo: angle to 0-180 range
        return (int16_t)(angle - config->minAngle);
    } else {
        // Bus servo: angle to 0-4095 range
        return config->centerPos + (int16_t)(angle * config->unitsPerDegree);
    }
}

/**
 * @brief Convert servo position to angle
 */
static float Servo_PositionToAngle(ServoConfig_t* config, int16_t position)
{
    if (config->type == 0) {
        // PWM servo: 0-180 to angle range
        return (float)position + config->minAngle;
    } else {
        // Bus servo: 0-4095 to angle range
        return (float)(position - config->centerPos) / config->unitsPerDegree;
    }
}

/**
 * @brief Quintic easing function for smooth motion
 */
static float QuinticEase(float t)
{
    float t2 = t * t;
    float t3 = t2 * t;
    float t4 = t3 * t;
    float t5 = t4 * t;
    return 10.0f * t3 - 15.0f * t4 + 6.0f * t5;
}

/**
 * @brief CPG (Central Pattern Generator) kernel function
 */
static float CPGKernel(float t)
{
    const float PI_F = 3.1415926f;
    return 0.5f * (1.0f - cosf(PI_F * t));
}

/**
 * @brief Blend quintic easing with CPG for natural motion
 */
static float BlendedProgress(float t)
{
    if (t <= 0.0f) return 0.0f;
    if (t >= 1.0f) return 1.0f;

    float quintic = QuinticEase(t);
    float cpg = CPGKernel(t);

    // Use CPG alpha from main.c (external variable)
    extern float cpgAlpha;
    extern uint8_t cpgEnabled;

    if (!cpgEnabled) return quintic;

    return (1.0f - cpgAlpha) * quintic + cpgAlpha * cpg;
}
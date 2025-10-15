/**
  ******************************************************************************
  * @file    servo.h
  * @brief   Servo control header for STM32 Nucleo G474RE
  * @description High-performance servo control with trajectory planning
  *              Supports PWM and UART bus servos with smooth motion profiles
  ******************************************************************************
  */

#ifndef __SERVO_H
#define __SERVO_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32g4xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/
/**
 * @brief Servo configuration structure
 */
typedef struct {
    uint8_t id;              // Servo ID (1-7)
    uint8_t type;            // 0 = PWM, 1 = Bus servo
    uint8_t channel;         // PWM channel or bus servo ID
    int16_t centerPos;       // Center position (PWM: 0-180, Bus: 0-4095)
    int16_t minPos;          // Minimum position
    int16_t maxPos;          // Maximum position
    float minAngle;          // Minimum angle in degrees
    float maxAngle;          // Maximum angle in degrees
    float unitsPerDegree;    // Position units per degree
    TIM_HandleTypeDef* htim; // Timer handle for PWM servos
    uint32_t timChannel;     // Timer channel for PWM servos
} ServoConfig_t;

/**
 * @brief Servo state structure
 */
typedef struct {
    float currentAngle;      // Current angle in degrees
    float targetAngle;       // Target angle in degrees
    int16_t currentPos;      // Current position (PWM: 0-180, Bus: 0-4095)
    int16_t targetPos;       // Target position
    uint32_t startTime;      // Motion start time (ms)
    uint32_t duration;       // Motion duration (ms)
    bool moving;             // True if servo is moving
} ServoState_t;

/* Exported constants --------------------------------------------------------*/
#define MAX_SERVOS 7
#define PWM_SERVOS 2
#define BUS_SERVOS 5

/* PWM Servo Configuration */
#define PWM_SERVO_1_CHANNEL TIM_CHANNEL_1
#define PWM_SERVO_2_CHANNEL TIM_CHANNEL_2
#define PWM_FREQUENCY 50      // 50Hz PWM frequency
#define PWM_PERIOD 20000      // 20ms period (1/PWM_FREQUENCY * 1000000)

/* Bus Servo Configuration */
#define BUS_SERVO_BAUDRATE 1000000  // 1Mbps
#define BUS_SERVO_CENTER_POS 2048   // Center position for 300° servos
#define BUS_SERVO_UNITS_PER_DEGREE (4096.0f / 300.0f)  // For 300° range

/* Exported functions --------------------------------------------------------*/
/**
 * @brief Initialize servo system
 * @param config: Array of servo configurations
 * @param state: Array of servo states
 * @param numServos: Number of servos to initialize
 */
void Servo_Init(ServoConfig_t* config, ServoState_t* state, uint8_t numServos);

/**
 * @brief Initialize UART for bus servo communication
 * @param huart: UART handle for bus servo communication
 */
void Servo_UART_Init(UART_HandleTypeDef* huart);

/**
 * @brief Center all servos to their center positions
 * @param config: Servo configuration array
 * @param state: Servo state array
 * @param numServos: Number of servos
 */
void Servo_CenterAll(ServoConfig_t* config, ServoState_t* state, uint8_t numServos);

/**
 * @brief Set target angle for a servo with trajectory planning
 * @param config: Servo configuration array
 * @param state: Servo state array
 * @param servoIndex: Index of the servo (0-6)
 * @param angle: Target angle in degrees
 * @param speedDegPerSec: Speed in degrees per second
 * @param durationMs: Motion duration in milliseconds
 */
void Servo_SetTargetAngle(ServoConfig_t* config, ServoState_t* state,
                         uint8_t servoIndex, float angle, float speedDegPerSec, uint32_t durationMs);

/**
 * @brief Update servo position using trajectory planning
 * @param config: Servo configuration array
 * @param state: Servo state array
 * @param servoIndex: Index of the servo to update
 * @param currentTime: Current system time in milliseconds
 * @return Progress value [0..1] where 1.0 means motion completed
 */
float Servo_UpdatePosition(ServoConfig_t* config, ServoState_t* state,
                          uint8_t servoIndex, uint32_t currentTime);

/**
 * @brief Get current position of a servo
 * @param config: Servo configuration array
 * @param state: Servo state array
 * @param servoIndex: Index of the servo
 * @return Current position in degrees
 */
int16_t Servo_GetPosition(ServoConfig_t* config, ServoState_t* state, uint8_t servoIndex);

/**
 * @brief Get positions of all servos
 * @param config: Servo configuration array
 * @param state: Servo state array
 * @param positions: Array to store positions (size MAX_SERVOS)
 * @param numServos: Number of servos
 */
void Servo_GetAllPositions(ServoConfig_t* config, ServoState_t* state,
                          int16_t* positions, uint8_t numServos);

/**
 * @brief Check if a servo is currently moving
 * @param state: Servo state array
 * @param servoIndex: Index of the servo
 * @return true if servo is moving
 */
bool Servo_IsMoving(ServoState_t* state, uint8_t servoIndex);

/**
 * @brief Stop all servo movements immediately
 * @param config: Servo configuration array
 * @param state: Servo state array
 * @param numServos: Number of servos
 */
void Servo_StopAll(ServoConfig_t* config, ServoState_t* state, uint8_t numServos);

#ifdef __cplusplus
}
#endif

#endif /* __SERVO_H */
/**
  ******************************************************************************
  * @file    communication.h
  * @brief   USB CDC Communication header for STM32 Nucleo G474RE
  * @description High-speed USB communication with command processing
  ******************************************************************************
  */

#ifndef __COMMUNICATION_H
#define __COMMUNICATION_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32g4xx_hal.h"
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>

/* Exported types ------------------------------------------------------------*/
/**
 * @brief Communication statistics
 */
typedef struct {
    uint32_t bytesReceived;
    uint32_t bytesTransmitted;
    uint32_t commandsProcessed;
    uint32_t errors;
    uint32_t lastError;
} CommStats_t;

/* Exported constants --------------------------------------------------------*/
#define COMM_BUFFER_SIZE 256
#define MAX_COMMAND_LENGTH 64
#define BAUD_RATE 115200

/* Exported functions --------------------------------------------------------*/
/**
 * @brief Initialize USB CDC communication
 */
void CDC_Init(void);

/**
 * @brief Check if data is available to read
 * @return true if data is available
 */
bool CDC_DataAvailable(void);

/**
 * @brief Read a single byte from USB CDC
 * @param data: Pointer to store the received byte
 * @return true if byte was read successfully
 */
bool CDC_ReadByte(uint8_t* data);

/**
 * @brief Transmit a single byte via USB CDC
 * @param data: Byte to transmit
 * @return true if byte was transmitted successfully
 */
bool CDC_TransmitByte(uint8_t data);

/**
 * @brief Transmit a null-terminated string via USB CDC
 * @param str: String to transmit
 * @return Number of bytes transmitted
 */
uint32_t CDC_TransmitString(const char* str);

/**
 * @brief Transmit a 32-bit unsigned integer as string
 * @param value: Value to transmit
 * @return Number of bytes transmitted
 */
uint32_t CDC_TransmitUInt32(uint32_t value);

/**
 * @brief Transmit a 32-bit signed integer as string
 * @param value: Value to transmit
 * @return Number of bytes transmitted
 */
uint32_t CDC_TransmitInt(int32_t value);

/**
 * @brief Transmit a floating point number as string
 * @param value: Value to transmit
 * @param precision: Number of decimal places
 * @return Number of bytes transmitted
 */
uint32_t CDC_TransmitFloat(float value, uint8_t precision);

/**
 * @brief Transmit binary data via USB CDC
 * @param data: Pointer to data buffer
 * @param length: Number of bytes to transmit
 * @return Number of bytes transmitted
 */
uint32_t CDC_TransmitData(uint8_t* data, uint32_t length);

/**
 * @brief Get communication statistics
 * @param stats: Pointer to statistics structure
 */
void CDC_GetStats(CommStats_t* stats);

/**
 * @brief Reset communication statistics
 */
void CDC_ResetStats(void);

/**
 * @brief Process incoming command buffer
 * @param buffer: Command buffer to process
 * @param length: Length of the command buffer
 */
void CDC_ProcessCommand(uint8_t* buffer, uint32_t length);

#ifdef __cplusplus
}
#endif

#endif /* __COMMUNICATION_H */
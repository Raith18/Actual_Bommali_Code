/**
  ******************************************************************************
  * @file    communication.c
  * @brief   USB CDC Communication implementation for STM32 Nucleo G474RE
  * @description High-speed USB communication with command processing
  ******************************************************************************
  */

/* Includes ------------------------------------------------------------------*/
#include "communication.h"
#include "usbd_cdc_if.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* Private defines -----------------------------------------------------------*/
#define TX_TIMEOUT 1000  // 1 second timeout for transmission
#define RX_TIMEOUT 10    // 10ms timeout for reception

/* Private variables ---------------------------------------------------------*/
static CommStats_t commStats = {0};
static char txBuffer[COMM_BUFFER_SIZE];
static char rxBuffer[COMM_BUFFER_SIZE];
static volatile uint32_t rxWriteIndex = 0;
static volatile uint32_t rxReadIndex = 0;
static volatile bool rxBufferFull = false;

/* Private function prototypes -----------------------------------------------*/
static void CDC_ProcessBuffer(void);
static uint32_t CDC_ParseAndExecute(const char* command);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize USB CDC communication
 */
void CDC_Init(void)
{
    // USB CDC is initialized in main.c via MX_USB_DEVICE_Init()
    // Reset statistics
    CDC_ResetStats();
}

/**
 * @brief Check if data is available to read
 */
bool CDC_DataAvailable(void)
{
    return (rxWriteIndex != rxReadIndex) || rxBufferFull;
}

/**
 * @brief Read a single byte from USB CDC
 */
bool CDC_ReadByte(uint8_t* data)
{
    if (!CDC_DataAvailable()) {
        return false;
    }

    *data = rxBuffer[rxReadIndex];
    rxReadIndex = (rxReadIndex + 1) % COMM_BUFFER_SIZE;

    if (rxBufferFull) {
        rxBufferFull = false;
    }

    return true;
}

/**
 * @brief Transmit a single byte via USB CDC
 */
bool CDC_TransmitByte(uint8_t data)
{
    if (CDC_TransmitData(&data, 1) == 1) {
        commStats.bytesTransmitted++;
        return true;
    }
    return false;
}

/**
 * @brief Transmit a null-terminated string via USB CDC
 */
uint32_t CDC_TransmitString(const char* str)
{
    uint32_t length = strlen(str);
    if (CDC_TransmitData((uint8_t*)str, length) == length) {
        commStats.bytesTransmitted += length;
        return length;
    }
    return 0;
}

/**
 * @brief Transmit a 32-bit unsigned integer as string
 */
uint32_t CDC_TransmitUInt32(uint32_t value)
{
    uint32_t length = snprintf(txBuffer, COMM_BUFFER_SIZE, "%lu", value);
    return CDC_TransmitString(txBuffer);
}

/**
 * @brief Transmit a 32-bit signed integer as string
 */
uint32_t CDC_TransmitInt(int32_t value)
{
    uint32_t length = snprintf(txBuffer, COMM_BUFFER_SIZE, "%ld", value);
    return CDC_TransmitString(txBuffer);
}

/**
 * @brief Transmit a floating point number as string
 */
uint32_t CDC_TransmitFloat(float value, uint8_t precision)
{
    uint32_t length = snprintf(txBuffer, COMM_BUFFER_SIZE, "%.*f", precision, value);
    return CDC_TransmitString(txBuffer);
}

/**
 * @brief Transmit binary data via USB CDC
 */
uint32_t CDC_TransmitData(uint8_t* data, uint32_t length)
{
    if (length == 0 || length > COMM_BUFFER_SIZE) {
        return 0;
    }

    // Use USB CDC transmit function
    if (CDC_Transmit_FS(data, length) == USBD_OK) {
        return length;
    }

    commStats.errors++;
    return 0;
}

/**
 * @brief Get communication statistics
 */
void CDC_GetStats(CommStats_t* stats)
{
    if (stats) {
        memcpy(stats, &commStats, sizeof(CommStats_t));
    }
}

/**
 * @brief Reset communication statistics
 */
void CDC_ResetStats(void)
{
    memset(&commStats, 0, sizeof(CommStats_t));
}

/**
 * @brief Process incoming command buffer
 */
void CDC_ProcessCommand(uint8_t* buffer, uint32_t length)
{
    if (length == 0 || length >= COMM_BUFFER_SIZE) {
        return;
    }

    // Null terminate the buffer
    buffer[length] = '\0';

    // Update statistics
    commStats.bytesReceived += length;
    commStats.commandsProcessed++;

    // Parse and execute command
    uint32_t responseLength = CDC_ParseAndExecute((char*)buffer);

    if (responseLength > 0) {
        commStats.bytesTransmitted += responseLength;
    }
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Parse and execute command
 */
static uint32_t CDC_ParseAndExecute(const char* command)
{
    // This is a simplified command parser
    // In a real implementation, this would parse the command and call appropriate functions

    // Echo the command back for now (can be extended)
    CDC_TransmitString("Echo: ");
    CDC_TransmitString(command);
    CDC_TransmitString("\r\n");

    return strlen(command) + 8; // Approximate response length
}

/**
 * @brief USB CDC Receive callback (called from USB interrupt)
 * @note This function should be called from the USB CDC receive callback
 */
void CDC_ReceiveCallback(uint8_t* Buf, uint32_t Len)
{
    for (uint32_t i = 0; i < Len; i++) {
        rxBuffer[rxWriteIndex] = Buf[i];
        rxWriteIndex = (rxWriteIndex + 1) % COMM_BUFFER_SIZE;

        if (rxWriteIndex == rxReadIndex) {
            rxBufferFull = true;
        }
    }

    commStats.bytesReceived += Len;
}

/**
 * @brief Get available space in RX buffer
 */
static uint32_t CDC_GetRxBufferSpace(void)
{
    if (rxBufferFull) {
        return 0;
    }

    if (rxWriteIndex >= rxReadIndex) {
        return COMM_BUFFER_SIZE - (rxWriteIndex - rxReadIndex) - 1;
    } else {
        return rxReadIndex - rxWriteIndex - 1;
    }
}

/**
 * @brief Check if RX buffer has complete line
 */
static bool CDC_HasCompleteLine(void)
{
    for (uint32_t i = rxReadIndex; i != rxWriteIndex; i = (i + 1) % COMM_BUFFER_SIZE) {
        if (rxBuffer[i] == '\n' || rxBuffer[i] == '\r') {
            return true;
        }
    }
    return false;
}
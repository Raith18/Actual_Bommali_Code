/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body for STM32 Nucleo G474RE Robotic Arm Controller
  * @description    : High-performance servo control with trajectory planning
  *                   Supports 2 PWM servos and 5 bus servos with smooth motion
  ******************************************************************************
  * Features:
  * - ARM Cortex-M4 @ 170MHz with FPU
  * - 7-channel servo control (2 PWM + 5 UART bus servos)
  * - Real-time trajectory planning with quintic easing
  * - USB CDC communication at 115200 baud
  * - CPG (Central Pattern Generator) support
  * - 50Hz real-time feedback
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "usb_device.h"
#include "usbd_cdc_if.h"
#include "servo.h"
#include "communication.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include <stdlib.h>
#include <math.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define RX_BUFFER_SIZE 64
#define TX_BUFFER_SIZE 128
#define MAX_SERVOS 7
#define PWM_SERVOS 2
#define BUS_SERVOS 5

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart1;
TIM_HandleTypeDef htim2;
PCD_HandleTypeDef hpcd_USB_OTG_FS;

/* USER CODE BEGIN PV */
/* Command processing */
static uint8_t rxBuffer[RX_BUFFER_SIZE];
static volatile uint8_t rxIndex = 0;
static uint8_t commandReady = 0;

/* Servo control */
ServoConfig_t servoConfig[MAX_SERVOS];
ServoState_t servoState[MAX_SERVOS];

/* Motion parameters */
float speedDegPerSec = 30.0f;
uint32_t motionDuration = 1200; // ms
uint8_t cpgEnabled = 0;
float cpgAlpha = 0.25f;

/* Real-time feedback */
uint8_t realTimeFeedback = 0;
uint32_t lastFeedbackTime = 0;
uint32_t feedbackInterval = 20; // 20ms = 50Hz

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_TIM2_Init(void);
static void MX_USB_OTG_FS_PCD_Init(void);

/* USER CODE BEGIN PFP */
void ProcessCommand(uint8_t* cmd);
void UpdateServoPositions(void);
void SendRealTimeFeedback(void);
float QuinticEase(float t);
float CPGKernel(float t);
float BlendedProgress(float t);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_TIM2_Init();
  MX_USB_OTG_FS_PCD_Init();
  MX_USB_DEVICE_Init();

  /* USER CODE BEGIN 2 */
  // Initialize USB CDC for communication
  CDC_Init();

  // Initialize servo system
  Servo_Init(servoConfig, servoState, MAX_SERVOS);

  // Start PWM timer
  HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_2);

  // Initialize bus servo communication
  Servo_UART_Init(&huart1);

  // Initialize servos to center positions
  Servo_CenterAll(servoConfig, servoState, MAX_SERVOS);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    // Process USB CDC data
    if (CDC_DataAvailable())
    {
      uint8_t data;
      if (CDC_ReadByte(&data))
      {
        if (data == '\n' || rxIndex >= RX_BUFFER_SIZE - 1)
        {
          rxBuffer[rxIndex] = '\0';
          commandReady = 1;
          rxIndex = 0;
        }
        else
        {
          rxBuffer[rxIndex++] = data;
        }
      }
    }

    // Process completed commands
    if (commandReady)
    {
      ProcessCommand(rxBuffer);
      commandReady = 0;
    }

    // Update servo positions
    UpdateServoPositions();

    // Send real-time feedback
    if (realTimeFeedback)
    {
      uint32_t currentTime = HAL_GetTick();
      if (currentTime - lastFeedbackTime >= feedbackInterval)
      {
        SendRealTimeFeedback();
        lastFeedbackTime = currentTime;
      }
    }

    // Small delay for system responsiveness
    HAL_Delay(5);
  }
  /* USER CODE END 3 */
}

/* USER CODE BEGIN 4 */
/**
  * @brief Process incoming command from USB CDC
  * @param cmd: Command string buffer
  */
void ProcessCommand(uint8_t* cmd)
{
  char* token;
  char cmd_copy[RX_BUFFER_SIZE];
  strncpy(cmd_copy, (char*)cmd, RX_BUFFER_SIZE - 1);
  cmd_copy[RX_BUFFER_SIZE - 1] = '\0';

  token = strtok(cmd_copy, " ");

  if (token == NULL) return;

  if (strcmp(token, "speed") == 0)
  {
    token = strtok(NULL, " ");
    if (token)
    {
      float speed = atof(token);
      if (speed >= 1.0f && speed <= 180.0f)
      {
        speedDegPerSec = speed;
        CDC_TransmitString("Speed set to: ");
        CDC_TransmitFloat(speedDegPerSec, 1);
        CDC_TransmitString(" deg/s\r\n");
      }
    }
  }
  else if (strcmp(token, "dur") == 0)
  {
    token = strtok(NULL, " ");
    if (token)
    {
      uint32_t duration = atoi(token);
      if (duration >= 100 && duration <= 10000)
      {
        motionDuration = duration;
        CDC_TransmitString("Duration set to: ");
        CDC_TransmitUInt32(motionDuration);
        CDC_TransmitString(" ms\r\n");
      }
    }
  }
  else if (strcmp(token, "cpg") == 0)
  {
    token = strtok(NULL, " ");
    if (token)
    {
      if (strcmp(token, "on") == 0)
      {
        cpgEnabled = 1;
        CDC_TransmitString("CPG enabled\r\n");
      }
      else if (strcmp(token, "off") == 0)
      {
        cpgEnabled = 0;
        CDC_TransmitString("CPG disabled\r\n");
      }
    }
  }
  else if (strcmp(token, "cpgalpha") == 0)
  {
    token = strtok(NULL, " ");
    if (token)
    {
      float alpha = atof(token);
      if (alpha >= 0.0f && alpha <= 1.0f)
      {
        cpgAlpha = alpha;
        CDC_TransmitString("CPG alpha set to: ");
        CDC_TransmitFloat(cpgAlpha, 2);
        CDC_TransmitString("\r\n");
      }
    }
  }
  else if (strcmp(token, "realtime") == 0)
  {
    token = strtok(NULL, " ");
    if (token)
    {
      if (strcmp(token, "on") == 0)
      {
        realTimeFeedback = 1;
        CDC_TransmitString("Real-time feedback enabled\r\n");
      }
      else if (strcmp(token, "off") == 0)
      {
        realTimeFeedback = 0;
        CDC_TransmitString("Real-time feedback disabled\r\n");
      }
    }
  }
  else if (strcmp(token, "readall") == 0)
  {
    // Send current positions of all servos
    int positions[MAX_SERVOS];
    Servo_GetAllPositions(servoConfig, servoState, positions, MAX_SERVOS);

    CDC_TransmitString("fb ");
    for (int i = 0; i < MAX_SERVOS; i++)
    {
      if (i > 0) CDC_TransmitString(",");
      CDC_TransmitInt(positions[i]);
    }
    CDC_TransmitString("\r\n");
  }
  else if (strcmp(token, "read") == 0)
  {
    token = strtok(NULL, " ");
    if (token)
    {
      int servoId = atoi(token);
      if (servoId >= 1 && servoId <= MAX_SERVOS)
      {
        int position = Servo_GetPosition(servoConfig, servoState, servoId - 1);
        CDC_TransmitString("fb ");
        CDC_TransmitInt(servoId);
        CDC_TransmitString(" ");
        CDC_TransmitInt(position);
        CDC_TransmitString("\r\n");
      }
    }
  }
  else
  {
    // Servo position command: "1 90" (servo_id angle)
    int servoId = atoi(token);
    token = strtok(NULL, " ");
    if (token && servoId >= 1 && servoId <= MAX_SERVOS)
    {
      int angle = atoi(token);
      Servo_SetTargetAngle(servoConfig, servoState, servoId - 1, angle, speedDegPerSec, motionDuration);
      CDC_TransmitString("Servo ");
      CDC_TransmitInt(servoId);
      CDC_TransmitString(" moving to: ");
      CDC_TransmitInt(angle);
      CDC_TransmitString("°\r\n");
    }
  }
}

/**
  * @brief Update all servo positions using trajectory planning
  */
void UpdateServoPositions(void)
{
  uint32_t currentTime = HAL_GetTick();

  for (int i = 0; i < MAX_SERVOS; i++)
  {
    if (servoState[i].moving)
    {
      float progress = Servo_UpdatePosition(servoConfig, servoState, i, currentTime);
      if (progress >= 1.0f)
      {
        servoState[i].moving = 0;
      }
    }
  }
}

/**
  * @brief Send real-time feedback of all servo positions
  */
void SendRealTimeFeedback(void)
{
  int positions[MAX_SERVOS];
  Servo_GetAllPositions(servoConfig, servoState, positions, MAX_SERVOS);

  CDC_TransmitString("rt ");
  for (int i = 0; i < MAX_SERVOS; i++)
  {
    if (i > 0) CDC_TransmitString(",");
    CDC_TransmitInt(positions[i]);
  }
  CDC_TransmitString("\r\n");
}

/**
  * @brief Quintic easing function for smooth motion
  * @param t: Progress value [0..1]
  * @return Eased progress value [0..1]
  */
float QuinticEase(float t)
{
  float t2 = t * t;
  float t3 = t2 * t;
  float t4 = t3 * t;
  float t5 = t4 * t;
  return 10.0f * t3 - 15.0f * t4 + 6.0f * t5;
}

/**
  * @brief CPG (Central Pattern Generator) kernel function
  * @param t: Progress value [0..1]
  * @return CPG progress value [0..1]
  */
float CPGKernel(float t)
{
  const float PI_F = 3.1415926f;
  return 0.5f * (1.0f - cosf(PI_F * t));
}

/**
  * @brief Blend quintic easing with CPG for natural motion
  * @param t: Progress value [0..1]
  * @return Blended progress value [0..1]
  */
float BlendedProgress(float t)
{
  if (t <= 0.0f) return 0.0f;
  if (t >= 1.0f) return 1.0f;

  float quintic = QuinticEase(t);
  if (!cpgEnabled) return quintic;

  float cpg = CPGKernel(t);
  return (1.0f - cpgAlpha) * quintic + cpgAlpha * cpg;
}

/* USER CODE END 4 */

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV6;
  RCC_OscInitStruct.PLL.PLLN = 85;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_SYSCLK_DIV1;
  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{
  /* USER CODE BEGIN TIM2_Init 0 */
  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM2_Init 1 */
  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 169; // 170MHz / 170 = 1MHz
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 19999; // 1MHz / 20000 = 50Hz PWM frequency
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 1500; // 1.5ms pulse (90° for most servos)
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */
  /* USER CODE END TIM2_Init 2 */
  HAL_TIM_MspPostInit(&htim2);
}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{
  /* USER CODE BEGIN USART1_Init 0 */
  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */
  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 1000000; // 1Mbps for bus servos
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */
  /* USER CODE END USART1_Init 2 */
}

/**
  * @brief USB_OTG_FS Initialization Function
  * @param None
  * @retval None
  */
static void MX_USB_OTG_FS_PCD_Init(void)
{
  /* USER CODE BEGIN USB_OTG_FS_Init 0 */
  /* USER CODE END USB_OTG_FS_Init 0 */

  /* USER CODE BEGIN USB_OTG_FS_Init 1 */
  /* USER CODE END USB_OTG_FS_Init 1 */
  hpcd_USB_OTG_FS.Instance = USB_OTG_FS;
  hpcd_USB_OTG_FS.Init.dev_endpoints = 6;
  hpcd_USB_OTG_FS.Init.speed = PCD_SPEED_FULL;
  hpcd_USB_OTG_FS.Init.phy_itface = PCD_PHY_EMBEDDED;
  hpcd_USB_OTG_FS.Init.Sof_enable = DISABLE;
  hpcd_USB_OTG_FS.Init.low_power_enable = DISABLE;
  hpcd_USB_OTG_FS.Init.lpm_enable = DISABLE;
  hpcd_USB_OTG_FS.Init.battery_charging_enable = ENABLE;
  hpcd_USB_OTG_FS.Init.vbus_sensing_enable = ENABLE;
  hpcd_USB_OTG_FS.Init.use_dedicated_ep1 = DISABLE;
  if (HAL_PCD_Init(&hpcd_USB_OTG_FS) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USB_OTG_FS_Init 2 */
  /* USER CODE END USB_OTG_FS_Init 2 */
}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */
  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_7, GPIO_PIN_RESET);

  /*Configure GPIO pin : PC7 */
  GPIO_InitStruct.Pin = GPIO_PIN_7;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */
  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN Callback Functions */
/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

/* USER CODE END Callback Functions */
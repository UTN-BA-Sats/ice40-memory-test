#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_task_wdt.h"
#include "fpga_ram_data.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

#define FPGA_HOST SPI2_HOST
#define PIN_NUM_MISO 27
#define PIN_NUM_MOSI 14
#define PIN_NUM_CLK 25
#define PIN_NUM_CS 26

#define PIN_NUM_RESET 13

#define FPGA_CLK_FREQ 1000000

#define FPGA_RESET_PULSE_WIDTH pdMS_TO_TICKS(500)

static const char TAG[] = "main";

static uint8_t rxbuf[10240] = {0};

void setup_reset_gpio() {
  gpio_config_t io_conf = {.intr_type = GPIO_INTR_DISABLE,
                           .mode = GPIO_MODE_OUTPUT,
                           .pin_bit_mask = 1ULL << PIN_NUM_RESET,
                           .pull_down_en = GPIO_PULLDOWN_DISABLE,
                           .pull_up_en = GPIO_PULLDOWN_DISABLE};

  ESP_ERROR_CHECK(gpio_config(&io_conf));

  gpio_set_level(PIN_NUM_RESET, 1);
}

void reset_fpga() {
  gpio_set_level(PIN_NUM_RESET, 0);
  vTaskDelay(FPGA_RESET_PULSE_WIDTH);
  gpio_set_level(PIN_NUM_RESET, 1);
}

esp_err_t check_signature_rom(spi_device_handle_t fpga_handle) {
  const uint8_t EXPECTED_DATA[] = {0x2b, 0xa7, 0x56, 0x8b};
  spi_transaction_t readtrans = {.addr = 0x2800, .rxlength = 32, .flags = SPI_TRANS_USE_RXDATA};

  esp_err_t ret = spi_device_polling_transmit(fpga_handle, &readtrans);
  if (ret != ESP_OK) {
    return ret;
  }

  if (memcmp(EXPECTED_DATA, readtrans.rx_data, sizeof(EXPECTED_DATA))) {
    ESP_LOGE(TAG, "check_signature_rom: expected %02x %02x %02x %02x but read %02x %02x %02x %02x", EXPECTED_DATA[0],
             EXPECTED_DATA[1], EXPECTED_DATA[2], EXPECTED_DATA[3], readtrans.rx_data[0], readtrans.rx_data[1],
             readtrans.rx_data[2], readtrans.rx_data[3]);
    return ESP_ERR_INVALID_RESPONSE;
  }

  return ESP_OK;
}

void app_main(void) {
  esp_err_t ret;

  ESP_LOGI(TAG, "Initializing bus SPI%d...", FPGA_HOST + 1);
  spi_bus_config_t buscfg = {
      .miso_io_num = PIN_NUM_MISO,
      .mosi_io_num = PIN_NUM_MOSI,
      .sclk_io_num = PIN_NUM_CLK,
      .quadwp_io_num = -1,
      .quadhd_io_num = -1,
      .max_transfer_sz = 10500,
  };
  ret = spi_bus_initialize(FPGA_HOST, &buscfg, SPI_DMA_CH_AUTO);
  ESP_ERROR_CHECK(ret);

  spi_device_interface_config_t devcfg = {
      .address_bits = 16,
      .dummy_bits = 8,
      .clock_speed_hz = FPGA_CLK_FREQ,
      .mode = 0,
      .spics_io_num = PIN_NUM_CS,
      .queue_size = 1,
      .flags = SPI_DEVICE_HALFDUPLEX,
      .input_delay_ns = 0,
  };

  spi_device_handle_t devhandle;

  ret = spi_bus_add_device(FPGA_HOST, &devcfg, &devhandle);
  ESP_ERROR_CHECK(ret);

  setup_reset_gpio();

  vTaskDelay(pdMS_TO_TICKS(500));

  while (1) {
    int errors = 0;
    spi_transaction_t readtrans = {.addr = 0, .rxlength = 8 * sizeof(FPGA_RAM), .rx_buffer = rxbuf};

    memset(rxbuf, 0, sizeof(rxbuf));

    ret = spi_device_polling_transmit(devhandle, &readtrans);

    if (ret == ESP_OK) {
      size_t i;
      for (i = 0; i < sizeof(FPGA_RAM); i++) {
        if (rxbuf[i] != FPGA_RAM[i]) {
          errors++;
        }
        taskYIELD();
      }
    } else {
      ESP_LOGE(TAG, "spi_device_polling_transmit failed with result %d", ret);
    }

    ESP_LOGI(TAG, "%d errors during RAM test", errors);
    if (errors > 0) {
      ESP_LOG_BUFFER_HEX(TAG, rxbuf, sizeof(rxbuf));
    }

    ret = check_signature_rom(devhandle);
    if (ret == ESP_ERR_INVALID_RESPONSE) {
      ESP_LOGE(TAG, "Invalid response from FPGA, resetting...");
      reset_fpga();
    } else if (ret != ESP_OK) {
      ESP_LOGE(TAG, "Unknown error");
    }

    vTaskDelay(pdMS_TO_TICKS(5000));
  }
}

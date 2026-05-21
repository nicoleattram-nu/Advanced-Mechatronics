#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include <math.h>

// SPI Defines
// We are going to use SPI 0, and allocate it to the following GPIO pins
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define SPI_PORT spi0
#define PIN_MISO 16
#define PIN_CS   17
#define PIN_SCK  18
#define PIN_MOSI 19

#define UPDATE_RATE_HZ 200
#define DT (1.0f / UPDATE_RATE_HZ)

static inline void cs_deselect(uint cs_pin);
static inline void cs_select(uint cs_pin);
void writeDAC(int channel, float voltage);


int main()
{
    stdio_init_all();

    // SPI initialisation. This example will use SPI at 1MHz.
    spi_init(SPI_PORT, 1000*1000);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_CS,   GPIO_FUNC_SIO);
    gpio_set_function(PIN_SCK,  GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    // Chip select is active-low, so we'll initialise it to a driven-high state
    gpio_set_dir(PIN_CS, GPIO_OUT);
    gpio_put(PIN_CS, 1);
    // For more examples of SPI use see https://github.com/raspberrypi/pico-examples/tree/master/spi

    float t = 0.0f;

    while (true) {
        printf("Hello, world!\n");
        float sin_voltage = (sinf(2.0f * M_PI * 2.0f * t) +1.0f ) / 2.0f * 3.3f;
        
        float phase = fmodf(t, 1.0f);          // 0 to 1 over 1 second
        float tri_voltage;
        if (phase < 0.5f) {
            tri_voltage = phase * 2.0f * 3.3f;         // rising: 0 -> 3.3V
        } else {
            tri_voltage = (1.0f - phase) * 2.0f * 3.3f; // falling: 3.3V -> 0
        }
            
        // channel: 0 = channel A, 1 = channel B
        writeDAC(0, sin_voltage);
        writeDAC(1, tri_voltage);
        t = t + DT; 
        sleep_ms(1000 / UPDATE_RATE_HZ); // sleep must match refresh rate
    }
}

static inline void cs_select(uint cs_pin) {
    asm volatile("nop \n nop \n nop"); // FIXME
    gpio_put(cs_pin, 0);
    asm volatile("nop \n nop \n nop"); // FIXME
}

static inline void cs_deselect(uint cs_pin) {
    asm volatile("nop \n nop \n nop"); // FIXME
    gpio_put(cs_pin, 1);
    asm volatile("nop \n nop \n nop"); // FIXME
}

void writeDAC(int channel, float voltage) { 
    uint8_t data[2];
    uint16_t binVolts = (uint16_t)(voltage / 3.3f * 1023);
    if (binVolts > 1023) binVolts = 1023;

    // Bit 15: channel (0=A, 1=B)
    // Bit 14: BUF (0 = unbuffered)
    // Bit 13: GA  (1 = 1x gain)
    // Bit 12: SHDN (1 = active)
    // Bits 11-2: 10-bit data
    data[0] = ((channel & 0x1) << 7) | (0 << 6) | (1 << 5) | (1 << 4);
    data[0] |= (binVolts >> 6) & 0x0F;
    data[1]  = (binVolts << 2) & 0xFF;

    cs_select(PIN_CS);
    spi_write_blocking(SPI_PORT, data, 2);
    cs_deselect(PIN_CS);

    // uint8_t data[2]; // this will hold info for the data wave we want to create
    // data[0] = 0b01110000; // 
    // data[1] = 0b11111100;

    // data[0] = data[0] | ((channel & 0b1) << 7); // place correct channel
    // uint16_t binVolts =  (uint16_t)(voltage / 3.3 * 1023); // turn input volts into binary num
    // if (binVolts > 1023) binVolts = 1023;
    // data[0] = data[0] | ((binVolts >> 6) & 0b00001111); // place data points

    // data[1] = ((binVolts << 2) & 0xFF);

    // cs_select(PIN_CS);
    // spi_write_blocking(SPI_PORT, data, 2); // where data is a uint8_t array with length len
    // cs_deselect(PIN_CS);
}

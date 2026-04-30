#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

// I2C defines
// This example will use I2C0 on GPIO8 (SDA) and GPIO9 (SCL) running at 400KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9

#define LED 25
#define ADDR 0b0100000

// MCP23008 Registers
#define IODIR 0x00 // pin direction
#define GPIO  0x09 // pins
#define OLAT  0x0A // output latch

void setPin(uint8_t address, uint8_t register, uint8_t value); // write function
uint8_t readPin(uint8_t address, uint8_t register); // read fucntion


int main()
{
    stdio_init_all();

    char buf[2];
    buf[0] = 0x0A; // OLAT
    buf[1] = 0b11111110; // only set GP7 tobe output

    gpio_init(LED); 
    gpio_set_dir(LED, GPIO_OUT);
    gpio_put(LED, 0); // start with LED off

    // I2C Initialisation. Using it at 400Khz.
    i2c_init(I2C_PORT, 400*1000);

    gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA);
    gpio_pull_up(I2C_SCL);
    // For more examples of I2C use see https://github.com/raspberrypi/pico-examples/tree/master/i2c

    setPin(ADDR, IODIR, 0b00111111); // Pin directions: GP0=input, GP1-GP7=output
    setPin(ADDR, OLAT, 0b11000000); // start with GP7 off

    while (true) {
        printf("still working...\r\n");
        
        // Proof-of-life before I2C
        for (int i = 0; i < 5; i++) {
            gpio_put(LED, 1); sleep_ms(100);
            gpio_put(LED, 0); sleep_ms(100);
        }

        unsigned char state = readPin(ADDR, GPIO); // read GPIO register
        bool gp0 = (state & (1 << 0)) != 0;       // isolate GP0
        printf("%d\r\n", state);

        // Button pulls GP0 low when pressed (pull-up resistor)
        if (!gp0) {
            setPin(ADDR, OLAT, 0b01000000); // GP6 on
        } else {
            setPin(ADDR, OLAT, 0b010000000); // GP6 off
        }

    }

    // // check pin 6 instead
    // while (true) {
    // setPin(ADDR, OLAT, 0b01000000); // GP6 on
    // sleep_ms(500);
    // setPin(ADDR, OLAT, 0b010000000); // GP6 off
    // sleep_ms(500);
    // }
}

void setPin(uint8_t address, uint8_t reg, uint8_t value){ // write function
    char buf[2];
    buf[0] = reg;
    buf[1] = value;
    i2c_write_blocking(I2C_PORT, address, buf, 2, false);
}

uint8_t readPin(uint8_t address, uint8_t reg){ // read fucntion 
    char buf[1];
    i2c_write_blocking(I2C_PORT, address, &reg, 1, true);  // true to keep host control of bus
    i2c_read_blocking(I2C_PORT, address, buf, 1, false);  // false - finished with bus

    return (uint8_t)buf[0];
}


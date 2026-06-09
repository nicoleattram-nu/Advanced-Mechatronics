#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

// I2C defines
// This example will use I2C0 on GPIO8 (SDA) and GPIO9 (SCL) running at 400KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9

#define LED 25 // default Pico2 LED
#define ADDR 0b0110110 // AS5600 encoder address 



uint16_t readAngle(uint8_t address); // read fucntion
void setPin(uint8_t address, uint8_t register, uint8_t value); // write function



int main()
{
    stdio_init_all();

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

    while (true) {
        printf("still working...\r\n"); // check serial monitor to show inside the while loop
        
        // Proof-of-life before I2C
        for (int i = 0; i < 5; i++) {
            gpio_put(LED, 1); sleep_ms(100);
            gpio_put(LED, 0); sleep_ms(100);
        }

        uint16_t angle = readAngle(ADDR); // read Raw Angle register
        float pos = angle * (360.0f/4096.0f);
        printf("Raw Angle: %d  Position: %.2f (deg) \r\n", angle, pos);

    }
}

uint16_t readAngle(uint8_t address){ // read fucntion 
    uint8_t buf[2]; // read two pins
    uint8_t reg = 0x0C; // first RAW An

    i2c_write_blocking(I2C_PORT, address, &reg, 1, true);  // true to keep host control of bus
    i2c_read_blocking(I2C_PORT, address, buf, 2, false);  // false - finished with bus

    return ((uint16_t)(buf[0] & 0x0F) << 8) | buf[1];
}

void setPin(uint8_t address, uint8_t reg, uint8_t value){ // write function
    char buf[2];
    buf[0] = reg;
    buf[1] = value;
    i2c_write_blocking(I2C_PORT, address, buf, 2, false);
}


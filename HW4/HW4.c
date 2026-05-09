#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "font.h"
#include "ssd1306.h"

// I2C defines
// This example will use I2C0 on GPIO8 (SDA) and GPIO9 (SCL) running at 400KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9

#define LED 25 // default LED
#define ADDR 0b0100000

// MCP23008 Registers
#define IODIR 0x00 // pin direction
#define GPIO  0x09 // pins
#define OLAT  0x0A // output latch

int main()
{
    
    stdio_init_all();
    sleep_ms(3000);  // wait 2 seconds for USB to connect
    printf("step 1 \r\n");

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

    printf("Scanning...\r\n");
    for (int addr = 0; addr < 128; addr++) {
        uint8_t buf;
        int ret = i2c_read_blocking(i2c0, addr, &buf, 1, false);
        if (ret >= 0) {
            printf("Found device at 0x%02X\r\n", addr);
        }
    }
    printf("Done\r\n");

    ssd1306_setup();

    char test_str[] = "print test";
    int x = 1;

    while (true) {
        printf("still working...\r\n");
        
        // Proof-of-life before I2C
        for (int i = 0; i < 5; i++) {
            gpio_put(LED, 1); sleep_ms(100);
            gpio_put(LED, 0); sleep_ms(100);
        }

        // scanf("%31s", user_str);
        drawString(x, 10, test_str);
        ssd1306_update();
        x = x+5; 
        sleep_ms(400);
        ssd1306_clear();

    }

    // // ssd1306_setup();

    // printf("Scanning I2C...\r\n");
    // for (int addr = 0; addr < 128; addr++) {
    //     uint8_t buf;
    //     int ret = i2c_read_blocking(I2C_PORT, addr, &buf, 1, false);
    //     if (ret >= 0) {
    //         printf("Found device at 0x%02X\r\n", addr);
    //     }
    // }
    // printf("Scan done.\r\n");

    // while(true) {} // stop here
}

void drawChar(int x, int y, char c) { // creates each letter 
    const char *bitmap = ASCII[c - 32];

    for (int col = 0; col < 5; col++) {
        for (int row = 0; row < 8; row++) {
            // check if bit 'row' is set in this column's bitmask
            if (bitmap[col] & (1 << row)) {
                ssd1306_drawPixel(x + col, y + row, 1);
            } else {
                ssd1306_drawPixel(x + col, y + row, 0); // optional background
            }
        }
    }
}

void drawString(int x, int y, const char *str) {
    while (*str) {
        drawChar(x, y, *str);
        x += 6; // 5 pixels wide + 1px spacing
        str++;
        }
    }

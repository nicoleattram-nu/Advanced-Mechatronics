#include <stdio.h>
#include <stdlib.h> 
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/adc.h"
#include "ssd1306.h"
#include "HW5.h"


// I2C defines
// This example will use I2C0 on GPIO8 (SDA) and GPIO9 (SCL) running at 400KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 8 // green 
#define I2C_SCL 9 // blue

#define LED 25 // Pico LED
#define ADDR 0b1101000

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

    mpu6050_init(); //initialize chip
    ssd1306_setup(); // turn on OLED

    // center of 128x32 display
    int cx = 64;  // center x
    int cy = 16;  // center y
    int scale = 50; // make the line move more quickly

    while (true) {
        printf("still working...\r\n");

        int16_t data[7]; // empty data set for desired values later 
        mpu6050_read(data);

        float ax   = data[0] * 0.000061f;
        float ay   = data[1] * 0.000061f;
        float az   = data[2] * 0.000061f;
        float temp = data[3] / 340.0f + 36.53f;
        float gx   = data[4] * 0.007630f;
        float gy   = data[5] * 0.007630f;
        float gz   = data[6] * 0.007630f;

        
        // // Proof-of-life before I2C
        // for (int i = 0; i < 5; i++) {
        //     gpio_put(LED, 1); sleep_ms(100);
        //     gpio_put(LED, 0); sleep_ms(100);
        // }
    

        // calculate end point of line
        int ex = cx + (int)(ax * scale);
        int ey = cy + (int)(ay * scale);

        ssd1306_clear();

        drawLine(cx, cy, ex, ey);  // draw from center to end point
        ssd1306_update();
        sleep_ms(10); 
        
    }
    
}

void drawLine(int cx, int cy, int ex, int ey) {
    int x_dist = abs(cx - ex); // get the absolute distance between center and end point 
    int y_dist = abs(cy - ey); // get the absolute distance between center and end point

    int step_x = (cx < ex) ? 1 : -1;  // step direction x: right or left
    int step_y = (cy < ey) ? 1 : -1;  // step direction y: up or down
    
    int err = x_dist - y_dist;  // error term to decide which way to step
    
    while (1) {
        ssd1306_drawPixel(cx, cy, 1);  // draw current pixel
        
        if (cx == ex && cy == ey) break;  // reached the end point
        
        int e2 = 2 * err;
        
        if (e2 > -y_dist) {  // step in x
            err -= y_dist;
            cx += step_x;
        }
        if (e2 < x_dist) {   // step in y
            err += x_dist;
            cy += step_y;
        }
    }
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

void mpu6050_init() { // initialize chip
    // check WHO_AM_I
    uint8_t check = readPin(ADDR, WHO_AM_I);
    if (check == 0x68 || check == 0x98) { // may be either depending on chip (I think?)
        setPin(ADDR, PWR_MGMT_1, 0x00);
        setPin(ADDR, ACCEL_CONFIG, 0x00);
        setPin(ADDR, GYRO_CONFIG, 0x18);
    } 
    else { // error: blink LED forever
        while (true) {
            gpio_put(LED, 1); sleep_ms(200);
            gpio_put(LED, 0); sleep_ms(200);
        }
    }
}

void mpu6050_read(int16_t *data) {
    uint8_t buf[14];
    uint8_t reg = ACCEL_XOUT_H;
    
    i2c_write_blocking(I2C_PORT, ADDR, &reg, 1, true);
    i2c_read_blocking(I2C_PORT, ADDR, buf, 14, false);

    // int16_t raw_ax = (buf[0] << 8) | buf[1];
    // int16_t raw_ay = (buf[2] << 8) | buf[3];
    // int16_t raw_az = (buf[4] << 8) | buf[5];
    // int16_t raw_t  = (buf[6] << 8) | buf[7];
    // int16_t raw_gx = (buf[8] << 8) | buf[9];
    // int16_t raw_gy = (buf[10] << 8) | buf[11];
    // int16_t raw_gz = (buf[12] << 8) | buf[13];

    for (int i = 0; i < 7; i++) {
        data[i] = (buf[i*2] << 8) | buf[i*2 + 1];
    }
}

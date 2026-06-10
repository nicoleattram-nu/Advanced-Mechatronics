#include <stdio.h>
#include "pico/stdlib.h"

#define SCK 16
#define DT 17

#define MAX_SAMPLES 2000

void initGPIO(int pin, int direction);

int main()
{
    stdio_init_all();
    initGPIO(SCK, 0);
    initGPIO(DT, 1);

    while (true) {
        printf("Hello, world!\n");
        sleep_ms(1000);
    }
}

void initGPIO(int pin, int direction) { // a function to initial GPIO pins
    if (direction == 1) { // input
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_IN);
        gpio_init(pin);
    }

    if (direction == 0) { // output
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_OUT);
        gpio_put(pin, 0); 
    }
}

int32_t hx711_read(void) {
    // Wait for DT to go low (data ready)
    while (gpio_get(DT)) tight_loop_contents();
 
    int32_t value = 0;
    
    // Read 24 bits
    for (int i = 0; i < 24; i++) {
        gpio_put(SCK, 1);
        sleep_us(1);
        value = (value << 1) | gpio_get(DT);
        gpio_put(SCK, 0);
        sleep_us(1);
    }
 
    // 25th pulse → gain 128, channel A
    gpio_put(SCK, 1);
    sleep_us(1);
    gpio_put(SCK, 0);
    sleep_us(1);
 
    // Sign-extend 24-bit → 32-bit
    if (value & 0x800000) value |= 0xFF000000;
    return value;
}
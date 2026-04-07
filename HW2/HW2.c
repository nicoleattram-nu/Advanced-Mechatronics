// SAMPLE CODE
#include <stdio.h> // set pico_enable_stdio_usb to 1 in CMakeLists.txt 
#include "pico/stdlib.h" // CMakeLists.txt must have pico_stdlib in target_link_libraries
#include "hardware/pwm.h" // CMakeLists.txt must have hardware_pwm in target_link_libraries
#include "hardware/adc.h" // CMakeLists.txt must have hardware_adc in target_link_libraries

#define PWMPIN 16
#define SERVOPIN 17 

// Sets the servo to a specific angle (0-180 degrees)
void servo_set_angle(uint pin, float angle) {
    // Clamp angle to valid range
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;

    // Map angle to pulse width in microseconds (1000us to 2000us)
    float pulse_us = 1000.0f + (angle / 180.0f) * 1000.0f;

    // Convert pulse width to PWM level
    // Wrap is 25000, period is 20ms (20000us), so: level = pulse_us / 20000 * 25000
    uint16_t level = (uint16_t)(pulse_us / 20000.0f * 25000.0f);

    pwm_set_gpio_level(pin, level);
}

void servo_init(uint pin) {
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(pin);

    // 150MHz / 120 = 1.25MHz
    // wrap at 25000 → 1.25MHz / 25000 = 50Hz (20ms period)
    pwm_set_clkdiv(slice_num, 120.0f);
    pwm_set_wrap(slice_num, 25000);
    pwm_set_enabled(slice_num, true);
}

bool timer_interrupt_function(__unused struct repeating_timer *t) {
    // read the adc
    uint16_t result1 = adc_read();
    // print the voltage
    printf("%f\r\n",(float)result1/4095*3.3);
    return true;
}

int main()
{
    stdio_init_all();
    printf("Starting...\r\n");

    // turn on a timer interrupt
    struct repeating_timer timer;
    // -100 means call the function every 100ms
    // +100 would mean call the function 100ms after the function has ended
    add_repeating_timer_ms(-100, timer_interrupt_function, NULL, &timer);

    // turn on the pwm, in this example to 10kHz with a resolution of 1500
    gpio_set_function(PWMPIN, GPIO_FUNC_PWM); // Set the Pin to be PWM
    uint slice_num = pwm_gpio_to_slice_num(PWMPIN); // Get PWM slice number
    // the clock frequency is 150MHz divided by a float from 1 to 255
    float div = 10; // must be between 1-255
    pwm_set_clkdiv(slice_num, div); // sets the clock speed
    uint16_t wrap = 1500; // when to rollover, must be less than 65535
    pwm_set_wrap(slice_num, wrap); 
    pwm_set_enabled(slice_num, true); // turn on the PWM

    pwm_set_gpio_level(PWMPIN, 1500/2); // set the duty cycle to 50%

    // turn on the adc
    adc_init();
    adc_gpio_init(26); // pin GP26 is pin ADC0
    adc_select_input(0); // sample from ADC0

    servo_init(SERVOPIN);
    // servo_set_angle(SERVOPIN, 90);

    while (true) {
        tight_loop_contents(); // do nothing here, the interrupt does the work
        // servo_set_angle(SERVOPIN, 120);

        for (int i = 0; i < 180; i ++) {
            servo_set_angle(SERVOPIN, i);
            sleep_ms(10);
        }

        for (int j = 180; j > 0; j = j-1) {
            servo_set_angle(SERVOPIN, j);
             sleep_ms(10);

        }

    }
}
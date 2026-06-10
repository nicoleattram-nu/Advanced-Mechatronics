#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"

#define SCK 16
#define DT 17

#define MAX_SAMPLES 2000

// ── Filter parameters ──────────────────────────────────────────────────────
float filter_state = 0.0f;
const float FILTER_ALPHA = 0.32f;  // ~15Hz cutoff at 20Hz sample rate

// ── Data structure ────────────────────────────────────────────────────────
typedef struct {
    int32_t  raw;           // raw HX711 reading
    int32_t  filtered;      // IIR filtered value
    uint32_t time_ms;       // timestamp in milliseconds
} sample_t;

sample_t samples[MAX_SAMPLES];
int num_samples = 0;

// ── Forward declarations ──────────────────────────────────────────────────
void initGPIO(int pin, int direction);
int32_t hx711_read(void);
int32_t iir_filter(int32_t raw);
void collect_samples(int n);
void send_samples(void);

// ── Main ──────────────────────────────────────────────────────────────────
int main()
{
    stdio_init_all();
    sleep_ms(2000);  // Wait for USB serial

    initGPIO(SCK, 0);  // output
    initGPIO(DT, 1);   // input

    printf("HX711 Data Collector ready.\n");
    printf("Send: COLLECT <num_samples>\n");
    
    char input[256];

    while (true) {
        if (stdio_usb_connected()) {
            printf("> ");
            fflush(stdout);
            
            if (fgets(input, sizeof(input), stdin) != NULL) {
                // Parse command
                if (strncmp(input, "COLLECT", 7) == 0) {
                    int n = atoi(input + 8);
                    collect_samples(n);
                    send_samples();
                }
            }
        }
        sleep_ms(100);
    }
    
    return 0;
}

// ── GPIO initialization ────────────────────────────────────────────────────
void initGPIO(int pin, int direction) {
    gpio_init(pin);
    
    if (direction == 0) {  // output
        gpio_set_dir(pin, GPIO_OUT);
        gpio_put(pin, 0);
    } else {  // input (direction == 1)
        gpio_set_dir(pin, GPIO_IN);
    }
}

// ── HX711 read 24-bit value ────────────────────────────────────────────────
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

// ── IIR low-pass filter ────────────────────────────────────────────────────
int32_t iir_filter(int32_t raw) {
    filter_state = FILTER_ALPHA * (float)raw + (1.0f - FILTER_ALPHA) * filter_state;
    return (int32_t)filter_state;
}

// ── Collect samples ────────────────────────────────────────────────────────
void collect_samples(int n) {
    if (n > MAX_SAMPLES) n = MAX_SAMPLES;
    
    printf("Collecting %d samples...\n", n);
    
    // Initialize filter with first reading
    filter_state = (float)hx711_read();
    
    for (int i = 0; i < n; i++) {
        uint32_t t_ms = time_us_32() / 1000;
        int32_t raw = hx711_read();
        int32_t filtered = iir_filter(raw);
        
        samples[i].raw = raw;
        samples[i].filtered = filtered;
        samples[i].time_ms = t_ms;
        
        // Print progress every 50 samples
        if ((i + 1) % 50 == 0) {
            printf("  %d/%d\r", i + 1, n);
            fflush(stdout);
        }
        
        sleep_ms(50);  // ~20 Hz sample rate
    }
    printf("\nCollection complete!\n");
    num_samples = n;
}

// ── Send data to PC ────────────────────────────────────────────────────────
void send_samples(void) {
    printf("DATA_START\n");
    for (int i = 0; i < num_samples; i++) {
        printf("%ld,%ld,%lu\n", 
               samples[i].raw,
               samples[i].filtered,
               samples[i].time_ms);
    }
    printf("DATA_END\n");
}
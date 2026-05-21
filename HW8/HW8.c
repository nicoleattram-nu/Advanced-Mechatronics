#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/dma.h"
#include <math.h>


// SPI Defines
// We are going to use SPI 0, and allocate it to the following GPIO pins
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define SPI_PORT spi0
#define PIN_MISO 16
#define PIN_CS_DAC 17
#define PIN_CS_RAM 20
#define PIN_SCK  18
#define PIN_MOSI 19

static inline void cs_deselect(uint cs_pin);
static inline void cs_select(uint cs_pin);
void writeDAC(int channel, float voltage);

void spi_ram_init();
void ram_write_sine();

void spi_ram_write(uint16_t, uint8_t *, int); 
void spi_ram_read(uint16_t, uint8_t *, int);

void update_dac (uint8_t channel, float voltage);
void update_dac_from_ram(int);


int main()
{
    stdio_init_all();

    // SPI initialisation. This example will use SPI at 1MHz.
    spi_init(SPI_PORT, 1000*1000);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_CS_DAC,   GPIO_FUNC_SIO);
    gpio_set_function(PIN_CS_RAM,   GPIO_FUNC_SIO);
    gpio_set_function(PIN_SCK,  GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);
    
    // Chip select is active-low, so we'll initialise it to a driven-high state
    gpio_set_dir(PIN_CS_DAC, GPIO_OUT);
    gpio_put(PIN_CS_DAC, 1);

    gpio_set_dir(PIN_CS_RAM, GPIO_OUT);
    gpio_put(PIN_CS_RAM, 1);
    // For more examples of SPI use see https://github.com/raspberrypi/pico-examples/tree/master/spi

    spi_ram_init();
    ram_write_sine();

    while (true) {
        for (int i = 0; i < 1024; i++) {
            update_dac_from_ram(i * 2);  // each sample is 2 bytes apart;
            sleep_ms(1);
        }
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

    cs_select(PIN_CS_DAC);
    spi_write_blocking(SPI_PORT, data, 2);
    cs_deselect(PIN_CS_DAC);
}




void spi_ram_init(){
    uint8_t data[2];
    int len = 2;
    data[0] = 0b00000001;
    data[1] = 0b01000000;

    cs_select(PIN_CS_RAM);
    spi_write_blocking(SPI_PORT, data, 2);
    cs_deselect(PIN_CS_RAM);
}

void spi_ram_write(uint16_t addr, uint8_t *data, int len) { 

    uint8_t packet[5];
    packet [0] = 0b0000010; // instruction, write
    packet [1] = addr<<8; // addr
    packet [2] = addr&0xFF; // addr
    packet [3] = data [0];
    packet [4] = data [1];

    cs_select (PIN_CS_RAM) ;
    spi_write_blocking(SPI_PORT, packet, 5); 
    cs_deselect(PIN_CS_RAM);

}

void update_dac_from_ram(int i){
    uint8_t data [2];
    spi_ram_read (i, data, 2);
    cs_select (PIN_CS_DAC);
    spi_write_blocking (SPI_PORT, data, 2);
    cs_deselect (PIN_CS_DAC) ;
}

void ram_write_sine(){

    int i = 0;
    uint8_t data [2];
    uint16_t data_short = 0;
    uint8_t channel = 0b0;
    float voltage = 0;
    uint16_t addr = 0;

    for (i=0; i<1024; i++) {
        data_short = (channel&0b1) <<15;
        data_short = data_short | (0b111<<12);
        voltage = (sin(2*3.14*i/1024.0)+1) *512;
        
        uint16_t v = (uint16_t)((sin(2 * M_PI * i / 1024.0) + 1.0) / 2.0 * 1023);
        if (v > 1023) v = 1023;
        data_short = ((channel & 0x1) << 15) | (0 << 14) | (1 << 13) | (1 << 12);
        data_short |= (v << 2);

        data[0] = data_short >> 8;
        data[1] = data_short & 0xFF;
        spi_ram_write(addr, data, 2);
        addr = addr + 2;
    }
}

void spi_ram_read(uint16_t addr, uint8_t * data, int len){
    uint8_t packet [5];
    packet [0] = 0b00000011; // instruction, read
    packet [1] = addr<<8; // addr
    packet [2] = addr&0xFF; // addr
    packet [3] = 0;
    packet [4] = 0;
    uint8_t dst [5];
    cs_select(PIN_CS_RAM) ;
    spi_write_read_blocking (SPI_PORT, packet, dst, 5); 
    cs_deselect (PIN_CS_RAM) ;
    data [0] = dst[3];
    data [1] = dst[4];
}

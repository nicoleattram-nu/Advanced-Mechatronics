#ifndef main_H__
#define main_H__

void gpio_callback(uint gpio, uint32_t events);
int8_t circle_x(void);
int8_t circle_y(void);

void setPin(uint8_t address, uint8_t reg, uint8_t value); // write function
uint8_t readPin(uint8_t address, uint8_t reg); // read fucntion
void drawLine(int cx, int cy, int ex, int ey);

void mpu6050_init(void);
void mpu6050_read(int16_t *data);


// MPU config registers
#define CONFIG 0x1A
#define GYRO_CONFIG 0x1B
#define ACCEL_CONFIG 0x1C
#define PWR_MGMT_1 0x6B
#define PWR_MGMT_2 0x6C
// MPU sensor data registers:
#define ACCEL_XOUT_H 0x3B
#define ACCEL_XOUT_L 0x3C
#define ACCEL_YOUT_H 0x3D
#define ACCEL_YOUT_L 0x3E
#define ACCEL_ZOUT_H 0x3F
#define ACCEL_ZOUT_L 0x40
#define TEMP_OUT_H   0x41
#define TEMP_OUT_L   0x42
#define GYRO_XOUT_H  0x43
#define GYRO_XOUT_L  0x44
#define GYRO_YOUT_H  0x45
#define GYRO_YOUT_L  0x46
#define GYRO_ZOUT_H  0x47
#define GYRO_ZOUT_L  0x48
#define WHO_AM_I     0x75

#endif
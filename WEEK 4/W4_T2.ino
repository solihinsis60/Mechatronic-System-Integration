#include <Wire.h>
#include <MPU6050.h>
#include <Servo.h>

MPU6050 mpu;
Servo servo;
int servoPosition = 90;

void setup() {
  servo.attach(9);
  servo.write(servoPosition); 
  
  pinMode(4, OUTPUT);  // Green LED
  pinMode(3, OUTPUT);  // Red LED
  
  // Start with Red LED ON and Green LED OFF
  digitalWrite(4, LOW);
  digitalWrite(3, HIGH);
  
  Serial.begin(9600);
  Wire.begin();
  mpu.initialize();
}

void loop() {
  // 1. Check for 'A' (Unlock) or 'D' (Lock) from Python
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'A') {
      servo.write(180);       // Unlock servo
      digitalWrite(4, HIGH); // Green LED ON
      digitalWrite(3, LOW);  // Red LED OFF
    } else if (command == 'D') {
      servo.write(90);        // Lock servo
      digitalWrite(4, LOW);  // Green LED OFF
      digitalWrite(3, HIGH); // Red LED ON
    }
  }

 
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  Serial.print(ax); Serial.print(",");
  Serial.print(ay); Serial.print(",");
  Serial.print(az); Serial.print(",");
  Serial.print(gx); Serial.print(",");
  Serial.print(gy); Serial.print(",");
  Serial.println(gz);
  
  delay(50);
}
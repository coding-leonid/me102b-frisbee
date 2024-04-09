from serial import Serial

esp32_ser = Serial('/dev/ttyUSB0', baudrate=115200, timeout=1)
try:
    while True:
        data = esp32_ser.readline().decode().strip()
        print(f"Received: {data}")
        esp32_ser.write("153\n".encode())

except KeyboardInterrupt:
    esp32_ser.close()
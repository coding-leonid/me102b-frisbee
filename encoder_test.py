import RPi.GPIO as GPIO

# Pins for the encoder outputs
PIN_A = 11
PIN_B = 13

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN_A, GPIO.IN)
GPIO.setup(PIN_B, GPIO.IN)

# Initialize variables
encoder_count = 0
last_encoded = 0

# Callback function to update encoder count
def update_encoder(channel):
    global encoder_count
    global last_encoded
    
    # Read current state of both encoder outputs
    a = GPIO.input(PIN_A)
    b = GPIO.input(PIN_B)
    
    # Combine the states of A and B into a single value
    encoded = (a << 1) | b
    
    # Determine direction of rotation and update encoder count accordingly
    if (last_encoded == 0b00 and encoded == 0b01) or \
       (last_encoded == 0b11 and encoded == 0b10):
        encoder_count += 1
    elif (last_encoded == 0b01 and encoded == 0b00) or \
         (last_encoded == 0b10 and encoded == 0b11):
        encoder_count -= 1
    print(encoder_count)    
    # Update last_encoded for the next iteration
    last_encoded = encoded

# Setup interrupt handlers for both encoder outputs
GPIO.add_event_detect(PIN_A, GPIO.BOTH, callback=update_encoder)
GPIO.add_event_detect(PIN_B, GPIO.BOTH, callback=update_encoder)

# Main loop (you can replace this with your actual program logic)
try:
    while True:
        # Do something here, or just sleep to keep the script running
        pass

except KeyboardInterrupt:
    # Clean up GPIO on Ctrl+C exit
    GPIO.cleanup()


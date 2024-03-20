import cv2
from serial import Serial
import threading
import numpy as np
#import RPi.GPIO as GPIO
from matplotlib import pyplot as plt
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

# Image size
IMG_SIZE : tuple[int, int] = (640, 480)
# Control proportionality constant
K_P : float = .5
# Use pretrained nano model
model : YOLO = YOLO('yolov8n.pt')
# Keep track of the latest range message
latest_range = int

def serial_callback(msg: float):
    global latest_range
    latest_range = msg
    print(f"New range value : {latest_range}")

def serial_reader() -> float:
    try:
        # Open serial port
        ser : Serial = Serial('/dev/ttyUSB0', baudrate=9600)
        ser.timeout = 1.
        while True:
            # Create a byte array to store received data
            data : bytearray = bytearray(11)
            # Read 11 bytes of data from the serial port
            for i in range(11):
                byte = ser.read()
                if len(byte) == 0:
                    break
                data[i] = ord(byte)
            # Calculate distance based on received data
            distance : float = (data[3] - 0x30) * 100 + (data[4] - 0x30) * 10 + (data[5] - 0x30) * 1 + \
                    (data[7] - 0x30) * 0.1 + (data[8] - 0x30) * 0.01 + (data[9] - 0x30) * 0.001
            # If bougus value or error, return -1
            if distance > 100 or distance < 0:
                distance = -1
            # Save the distance value
            serial_callback(distance)
            # Exit when exit flag is true
            if should_exit.is_set():
                break

    except Exception as e:
        # Handle any exceptions
        print(f"Exception thrown in serial thread: {e}")
    finally:
        # Close the port if something went wrong
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print("Serial port closed")
    
# Start the serial reader thread
serial_thread = threading.Thread(target=serial_reader)
serial_thread.daemon = True  # Set the thread as daemon so it exits when the main thread exits
serial_thread.start()
should_exit = threading.Event() # Trigger exit when 'q' is pressed in main thread

# Keep capturing while capture device is open
cap = cv2.VideoCapture(0)
while cap.isOpened():
    # Read and show current frame
    ret, frame = cap.read()
    # Exit if no return value
    if not ret:
        break
    # YOLO person trackning
    results = model.track(frame, persist=False, classes=[0], verbose=False)
    # If we detect people, extract IDs, draw bounding boxes
    if results[0].boxes.id != None:
        # Extract top left and bottom right corner
        boxes = results[0].boxes.xyxy.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        annotator = Annotator(frame, line_width=2, example='test')
        
        # Add bounding boxes, labels and centerpoints
        for box, track_id in zip(boxes, track_ids):
            annotator.box_label(box, label=f'Person {track_id}', color=(0, 255, 0))
            box = box.tolist()
            center_x = int((box[0] + box[2]) / 2)
            center_y = int((box[1] + box[3]) / 2)
            cv2.circle(frame, center=(center_x, center_y), radius=5, color=(0,0,255), thickness=-1)
        
        # No control unless exactly one person in frame
        if len(track_ids) == 1:
            err = center_x - IMG_SIZE[0] / 2
            pwm = np.sign(err) * np.min([K_P * np.abs(err), 100])
            print(pwm)

    cv2.imshow('Person tracker', frame)

    # Quit capturing when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        should_exit.set()
        break


serial_thread.join()
cap.release()
cv2.destroyAllWindows()
print("Exited both threads successfully")
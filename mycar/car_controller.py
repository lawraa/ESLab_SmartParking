from car_control.vehicles import PiRacerPro
from car_control.gamepads import MyGamepad
import display_live
import threading
import global_state
from ble_client import continuous_scan, get_tof_distance
import time

#from ..BLE_Connection.test import get_tof_distance
# def emergency_stop_func():
#     global emergency_stop
#     emergency_stop = True

# def tof_monitoring_thread():
#     global emergency_stop
#     while True:
#         current_tof_distance = get_tof_distance()
#         if current_tof_distance is not None and current_tof_distance < SAFE_DISTANCE_MM:
#             emergency_stop_func()
#         time.sleep(0.1)  # Adjust the sleep time as needed

# def driving_mode_logic(piracer, gamepad_input):
#     global emergency_stop
#     if emergency_stop:
#         piracer.set_throttle_percent(0.0)
#         return

# Flask web server related function
def run_flask_app():
    display_live.app.run(host='172.20.10.2', port=8082)

# Modes and constants
MODE_DRIVING = 'Driving'
MODE_PARKING = 'Parking'
MODE_OVERRIDE = 'Override'
SAFE_DISTANCE_MM = 100  # Safe distance in millimeters

# Logic for override mode control of PiRacer
def override_mode_logic(piracer, gamepad_input):
    print("In Override Mode")
    steering = gamepad_input.analog_stick_left.x
    throttle = gamepad_input.analog_stick_right.y * 0.5
    piracer.set_throttle_percent(throttle)
    piracer.set_steering_percent(steering)

# Logic for driving mode control of PiRacer
def driving_mode_logic(piracer, gamepad_input):
    print("In Driving Mode")
    current_tof_distance = get_tof_distance()  # Get current Time-of-Flight distance
    steering = gamepad_input.analog_stick_left.x
    piracer.set_steering_percent(steering)
    # Throttle control logic considering TOF distance
    if current_tof_distance is not None:
        if current_tof_distance > SAFE_DISTANCE_MM or (gamepad_input.analog_stick_right.y * 0.5) > 0:
            throttle = gamepad_input.analog_stick_right.y * 0.5
        else:
            throttle = 0.0
    else:
        throttle = gamepad_input.analog_stick_right.y * 0.5
    piracer.set_throttle_percent(throttle)

# Logic for parking mode control of PiRacer
def parking_mode_logic(piracer, gamepad_input):
    print("In Parking Mode")
    current_tof_distance = get_tof_distance()  # Get current Time-of-Flight distance
    steering = gamepad_input.analog_stick_left.x
    piracer.set_steering_percent(steering)
    # Throttle control logic considering TOF distance
    if current_tof_distance is not None:
        if current_tof_distance > SAFE_DISTANCE_MM or (gamepad_input.analog_stick_right.y * 0.22) > 0:
            throttle = gamepad_input.analog_stick_right.y * 0.22
        else:
            throttle = 0.0
    else:
        throttle = gamepad_input.analog_stick_right.y * 0.22
    piracer.set_throttle_percent(throttle)

# Main execution block
if __name__ == '__main__':
    mode = MODE_DRIVING
    global_state.global_state.mode = mode 
    my_gamepad = MyGamepad()
    my_gamepad.show_map()
    piracer = PiRacerPro()
    # Starting Flask web server and BLE scanning in separate threads
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
    ble_thread = threading.Thread(target=continuous_scan)
    ble_thread.start()

    print("ble_thread start")
    # Main loop for gamepad input handling and mode switching
    while True:
        gamepad_input = my_gamepad.read_data()
        # Mode switching logic based on gamepad button presses
        if gamepad_input.button_b == 1:  # Check if 'B' button is pressed
            if mode == MODE_DRIVING:
                mode = MODE_PARKING
                global_state.global_state.mode = "Parking"
                print("Change to Parking Mode")
            else:
                mode = MODE_DRIVING
                global_state.global_state.mode = "Driving"
                print("Change to Driving Mode")
        if gamepad_input.button_y == 1:
            if mode == MODE_DRIVING or MODE_PARKING:
                mode = MODE_OVERRIDE
                global_state.global_state.mode = "Override"
                print("Change to Override Mode")
            else:
                mode = MODE_DRIVING
                global_state.global_state.mode = "Driving"
                print("Change to Driving Mode")


        if mode == MODE_DRIVING:
            driving_mode_logic(piracer, gamepad_input)
        elif mode == MODE_PARKING:
            parking_mode_logic(piracer, gamepad_input)
        elif mode == MODE_OVERRIDE:
            override_mode_logic(piracer, gamepad_input)


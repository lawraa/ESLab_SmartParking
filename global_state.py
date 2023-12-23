import threading

class GlobalState:
    def __init__(self):
        # Initialize the default state
        self.mode = "Driving"  # Initial mode of operation
        self.emergency_stop = False  # Flag for emergency stop
        self.tof_distance = None  # Variable for ToF distance
        self.lock = threading.Lock()  # Lock for thread-safe operations

    def update_tof_distance(self, new_distance):
        # Update the ToF distance
        self.tof_distance = new_distance

    def get_tof_distance(self):
        # Retrieve the current ToF distance
        return self.tof_distance

    def set_emergency_stop(self, status: bool):
        # Set the emergency stop status
        self.emergency_stop = status

    # You can uncomment and add more methods here to update other sensor data or state variables

# Create a global instance of GlobalState
global_state = GlobalState()

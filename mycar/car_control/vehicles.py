import math
import time
import busio
import sys
print(sys.executable)
from abc import abstractmethod
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_ina219 import INA219
from adafruit_ssd1306 import SSD1306_I2C

class PiRacerBase:
    """
    Base class for PiRacer vehicles -> PiRacer Pro models.
    """
    # Constants for PWM (Pulse Width Modulation) control
    PWM_RESOLUTION = 16
    PWM_MAX_RAW_VALUE = math.pow(2, PWM_RESOLUTION) - 1
    PWM_FREQ_50HZ = 50.0
    PWM_WAVELENGTH_50HZ = 1.0 / PWM_FREQ_50HZ
    PWM_FREQ_500HZ = 500.0
    PWM_WAVELENGTH_500HZ = 1.0 / PWM_FREQ_500HZ

    @classmethod
    def _set_channel_active_time(cls, time: float, pwm_controller: PCA9685, channel: int) -> None:
        """
        Sets the active time (duty cycle) for a specific PWM channel.
        """
        raw_value = int(cls.PWM_MAX_RAW_VALUE * (time / cls.PWM_WAVELENGTH_50HZ))
        pwm_controller.channels[channel].duty_cycle = raw_value

    @classmethod
    def _get_50hz_duty_cycle_from_percent(cls, value: float) -> float:
        """
        Converts a percentage value to a duty cycle time for a 50Hz PWM signal.
        """
        return 0.0015 + (value * 0.0005)

    def __init__(self) -> None:
        """
        Initializes the PiRacer with I2C bus and display setup.
        """
        self.i2c_bus = busio.I2C(SCL, SDA)
        self.display = SSD1306_I2C(128, 32, self.i2c_bus, addr=0x3c)

    def _warmup(self) -> None:
        """
        Performs a warmup routine by setting steering and throttle to neutral.
        """
        self.set_steering_percent(0.0)
        self.set_throttle_percent(0.0)
        time.sleep(2.0)

    def get_battery_voltage(self) -> float:
        """
        Returns the current battery voltage.
        """
        return self.battery_monitor.bus_voltage + self.battery_monitor.shunt_voltage

    def get_battery_current(self) -> float:
        """
        Returns the current battery current in milliamperes.
        """
        return self.battery_monitor.current

    def get_power_consumption(self) -> float:
        """
        Returns the current power consumption of the system in watts.
        """
        return self.battery_monitor.power

    def get_display(self) -> SSD1306_I2C:
        """
        Returns the display object for drawing on the OLED screen.
        """
        return self.display

    @abstractmethod
    def set_steering_percent(self, value: float) -> None:
        """
        Abstract method to set the steering percentage. Implementation is model-specific.
        """
        pass

    @abstractmethod
    def set_throttle_percent(self, value: float) -> None:
        """
        Abstract method to set the throttle percentage. Implementation is model-specific.
        """
        pass

class PiRacerPro(PiRacerBase):
    """
    PiRacer Pro model
    """
    PWM_STEERING_CHANNEL = 0  # PWM channel for steering
    PWM_THROTTLE_CHANNEL = 1  # PWM channel for throttle

    def __init__(self) -> None:
        """
        Initializes the PiRacer Pro with specific configurations for PWM and battery monitor.
        """
        super().__init__()
        self.pwm_controller = PCA9685(self.i2c_bus, address=0x40)
        self.pwm_controller.frequency = self.PWM_FREQ_50HZ
        self.battery_monitor = INA219(self.i2c_bus, addr=0x42)
        self._warmup()

    def set_steering_percent(self, value: float) -> None:
        """
        Sets the steering percentage for the PiRacer Pro. Converts the percentage to 
        the appropriate PWM signal.
        """
        self._set_channel_active_time(self._get_50hz_duty_cycle_from_percent(-value),
                                      self.pwm_controller, self.PWM_STEERING_CHANNEL)

    def set_throttle_percent(self, value: float) -> None:
        """
        Sets the throttle percentage for the PiRacer Pro. Converts the percentage to 
        the appropriate PWM signal.
        """
        self._set_channel_active_time(self._get_50hz_duty_cycle_from_percent(value),
                                      self.pwm_controller, self.PWM_THROTTLE_CHANNEL)

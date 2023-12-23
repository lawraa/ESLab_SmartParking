# Copyright (C) 2022 twyleg
import os
import cv2
from picamera2 import Picamera2, Preview
from libcamera import Transform


class PiCamera2:
    def __init__(self):
        config_dict = {"size": (160, 120), "format": "BGR888"}
        transform = Transform(hflip=True, vflip=True)
        self.camera = Picamera2()
        self.camera_config = self.camera.create_preview_configuration(config_dict, transform=transform)
        self.camera.align_configuration(self.camera_config)
        self.camera.configure(self.camera_config)

    def __del__(self):
        self.camera.stop_preview()

    def capture_image(self, file_path):
        self.camera.capture_file(file_path)

    def start_recording(self, file_path):
        self.camera.start_recording(file_path)

    def stop_recording(self):
        self.camera.stop_recording()
    def show_camera_feed(self):
        self.camera.start()
        while True:
            frame = self.camera.capture_array() # Capture a frame as an array
            cv2.imshow('Camera Feed', frame)     # Display the frame

            if cv2.waitKey(1) & 0xFF == ord('q'): # Exit loop if 'q' is pressed
                break
        
        self.camera.stop()
        cv2.destroyAllWindows()


"""
class PiCamera(BaseCamera):
    def __init__(self, image_w=160, image_h=120, image_d=3,
                 vflip=False, hflip=False):
        from picamera2 import Picamera2
        from libcamera import Transform

        # it's weird but BGR returns RGB images
        config_dict = {"size": (image_w, image_h), "format": "BGR888"}
        transform = Transform(hflip=hflip, vflip=vflip)
        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            config_dict, transform=transform)
        self.camera.align_configuration(config)
        self.camera.configure(config)
        # try min / max frame rate as 0.1 / 1 ms (it will be slower though)
        self.camera.set_controls({"FrameDurationLimits": (100, 1000)})
        self.camera.start()

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True
        self.image_d = image_d

        # get the first frame or timeout
        logger.info('PiCamera opened...')
        warming_time = time.time() + 5  # quick after 5 seconds
        while self.frame is None and time.time() < warming_time:
            logger.info("...warming camera")
            self.run()
            time.sleep(0.2)

        if self.frame is None:
            raise CameraError("Unable to start PiCamera.")

        logger.info("PiCamera ready.")

    def run(self):
        # grab the next frame from the camera buffer
        self.frame = self.camera.capture_array("main")
        if self.image_d == 1:
            self.frame = rgb2gray(self.frame)

        return self.frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        while self.on:
            self.run()

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        logger.info('Stopping PiCamera')
        time.sleep(.5)
        self.camera.close()
        self.camera = None
"""
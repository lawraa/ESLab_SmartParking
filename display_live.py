from flask import Flask, Response
import cv2
from picamera2 import Picamera2
from libcamera import Transform
import global_state

app = Flask(__name__)

# Font settings for annotations on the video
font = cv2.FONT_HERSHEY_SIMPLEX
position = (0, 0)  # Desired position for text
font_scale = 0.75
font_color = (255, 255, 255)  # Color of the font (white)
line_type = 2

def gen_frames():
    # Configuration for camera, including flipping the image
    transform = Transform(hflip=True, vflip=True)
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": (320, 240), "format": "RGB888"}, transform=transform)
    picam2.configure(video_config)
    picam2.start()

    # Loop to capture and annotate frames
    while True:
        frame = picam2.capture_array()

        # Retrieve and format sensor data for annotation
        mode_text = f"{global_state.global_state.mode}"
        tof_distance_text = "Connecting"
        if global_state.global_state.tof_distance:
            if global_state.global_state.tof_distance > 400:
                tof_distance_text = "Safe"
            elif global_state.global_state.tof_distance > 100:
                tof_distance_text = f"Safety Dist: {global_state.global_state.tof_distance} mm"
            else:
                tof_distance_text = f"Emergency Stop: {global_state.global_state.tof_distance} mm"

        # Annotate the frame with text
        cv2.putText(frame, mode_text, (20, 25), font, 0.5, font_color, line_type)
        cv2.putText(frame, tof_distance_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Additional annotation - a colored dot
        dot_position = (10, 20)
        dot_color = (255, 0, 0)  # Default color
        if mode_text == "Driving":
            dot_color = (0, 255, 0)  # Green for Driving
        elif mode_text == "Parking":
            dot_color = (0, 0, 255)  # Red for Parking

        dot_radius = 5
        cv2.circle(frame, dot_position, dot_radius, dot_color, -1)

        # Encode the frame for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Stream the video feed
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start the Flask application
    # Change to your own IP to use
    app.run(host='172.20.10.2', port=8082)

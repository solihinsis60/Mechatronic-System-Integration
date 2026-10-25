import matplotlib

matplotlib.use('TkAgg')

import serial
import time
import threading
import numpy as np
import matplotlib.pyplot as plt


class MotionSecuritySystem:
    def __init__(self, port='COM3', baud=9600):
        self.port_name = port
        self.baud_rate = baud
        self.allowed_tags = {"0006547089"}
        self.latest_tag = ""

        # Initialize Serial and Matplotlib
        self.serial_conn = serial.Serial(self.port_name, self.baud_rate, timeout=0.1)
        time.sleep(2)
        self.serial_conn.reset_input_buffer()
        self.serial_conn.write(b'D')

        plt.ion()
        self.fig, self.ax = plt.subplots()

    def _tag_listener(self):
        """Background worker to capture RFID input from terminal."""
        while True:
            user_input = input("\nTap RFID card (or 'q' to quit): ").strip().upper()
            self.latest_tag = user_input

    @staticmethod
    def _validate_circular_motion(x_coords, y_coords):
        """Calculates radius and angular sweep to verify circular gesture."""
        if len(x_coords) < 10:
            return False

        arr_x = np.array(x_coords)
        arr_y = np.array(y_coords)

        mean_radius = np.mean(np.hypot(arr_x - np.mean(arr_x), arr_y - np.mean(arr_y)))
        wrapped_angles = np.unwrap(np.arctan2(arr_y - np.mean(arr_y), arr_x - np.mean(arr_x)))
        angular_span = np.degrees(np.ptp(wrapped_angles))

        print(f"Radius: {mean_radius:.0f}, Angle: {angular_span:.0f} deg")
        return mean_radius > 1000 and angular_span > 160

    def start(self):
        # Start background RFID input thread
        threading.Thread(target=self._tag_listener, daemon=True).start()

        x_history, y_history = [], []

        try:
            while True:
                raw_data = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()

                if raw_data:
                    parts = raw_data.split(',')
                    if len(parts) >= 2:
                        try:
                            px = int(parts[0])
                            py = int(parts[1])

                            x_history.append(px)
                            y_history.append(py)
                            x_history = x_history[-30:]
                            y_history = y_history[-30:]

                            self.ax.clear()
                            self.ax.plot(x_history, y_history, 'ro-')
                            self.ax.set_xlim(-40000, 40000)
                            self.ax.set_ylim(-40000, 40000)
                            self.ax.set_title("MPU6050 Real-Time Motion")
                            self.ax.grid(True)
                        except ValueError:
                            pass

                plt.pause(0.01)

                # Process RFID authentication trigger
                if self.latest_tag:
                    tag = self.latest_tag
                    self.latest_tag = ""

                    if tag == 'Q':
                        break
                    elif tag in self.allowed_tags:
                        print("RFID authorized! Perform circular motion for 3 seconds...")
                        x_history, y_history = [], []
                        self.serial_conn.reset_input_buffer()
                        recording_start = time.time()

                        while time.time() - recording_start < 3.0:
                            stream_line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                            if stream_line:
                                tokens = stream_line.split(',')
                                if len(tokens) >= 2:
                                    try:
                                        x_history.append(int(tokens[0]))
                                        y_history.append(int(tokens[1]))

                                        self.ax.clear()
                                        self.ax.plot(x_history, y_history, 'ro-')
                                        self.ax.set_xlim(-40000, 40000)
                                        self.ax.set_ylim(-40000, 40000)
                                        self.ax.set_title("Recording Circular Motion...")
                                        self.ax.grid(True)
                                    except ValueError:
                                        pass
                            plt.pause(0.01)

                        if self._validate_circular_motion(x_history, y_history):
                            print("Motion verified. Access granted.")
                            self.serial_conn.write(b'A')
                        else:
                            print("Motion invalid. Access denied.")
                            self.serial_conn.write(b'D')
                    else:
                        print("UID unauthorized. Access denied.")
                        self.serial_conn.write(b'D')

        except KeyboardInterrupt:
            print("Program terminated.")
        finally:
            self.serial_conn.write(b'D')
            self.serial_conn.close()
            plt.ioff()
            plt.close('all')


if __name__ == '__main__':
    system = MotionSecuritySystem(port='COM3', baud=9600)
    system.start()
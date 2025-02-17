# from pygame import joystick, time as pgtime
import time

import pygame as pg

from tools import Tools
from settings import JoystickSettings as js, ColorPalette as clr


import cv2, glob
import mediapipe as mp
import numpy as np

import threading


class HandWatch:
    DEVICE_ID = 51
    # FRAME_WIDTH = 1280
    # FRAME_HEIGHT = 720
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 360

    HAND_DETECTOR = mp.solutions.hands
    DRAW_UTILS = mp.solutions.drawing_utils

    def __init__(self, engine):
        self.engine = engine
        self.capture = None

        # self.draw_utils = mp.solutions.drawing_utils
        self.hands = None

        self.pg_srf = None

        # control parameters
        self._thrust_on = False
        self._spray_on = False
        self._thrust_force = 0  # -1, 0, 1
        self._spray_force = 0  # -1, 0, 1
        self._ballast_fill = 50  # 0, 50, 100

        # Activation flag, changed by pressing key button 'h' ('hand')
        self.active = False

        self.success = self._initiate()


    def _initiate(self):
        try:
            cap = cv2.VideoCapture(self.DEVICE_ID)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)
            # cap.set(cv2.CAP_PROP_FPS, 30)

            hands = self.HAND_DETECTOR.Hands(static_image_mode=False, min_detection_confidence=0.7, max_num_hands=1)

            if cap is not None and hands is not None:
                self.capture = cap
                self.hands = hands

                self.capture_thread = threading.Thread(target=self.capture_and_analize)
                self.capture_thread.start()

                return True
            else:
                print("Unable to initialte Hand Watch. Capture / hands returned None.")
                return False
        except Exception as e:
            print(f"Unable to initiate Hand Watch: {e}")
            return False

    def update(self):
        if self.active and self.hands is not None:
            ...

    def capture_and_analize(self):
        print("Capture Thread started...")
        while self.engine.is_running:
            if self.success and self.active:
                success, frame = self.capture.read()
                if success:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    clear_screen = np.zeros((self.FRAME_HEIGHT, self.FRAME_WIDTH, 3), dtype=np.uint8)

                    result = self.hands.process(frame_rgb)
                    if result.multi_hand_landmarks is not None:
                        for hand in result.multi_hand_landmarks:
                            self.DRAW_UTILS.draw_landmarks(clear_screen, hand, self.HAND_DETECTOR.HAND_CONNECTIONS)

                    # frame_surface = pg.surfarray.make_surface(frame_rgb).convert()
                    frame_surface = pg.surfarray.make_surface(clear_screen).convert()
                    frame_surface.set_colorkey(clr.BLACK)
                    frame_surface = pg.transform.flip(frame_surface, True, True)
                    frame_surface = pg.transform.rotate(frame_surface, 90)

                    # scale_factor = 0.5  # 50% scale
                    # # Calculate the new width and height after scaling
                    # new_width = int(frame_surface.get_width() * scale_factor)
                    # new_height = int(frame_surface.get_height() * scale_factor)

                    # scaled_surface = pg.transform.scale(frame_surface, (new_width, new_height))
                    self.pg_srf = frame_surface

            else:
                time.sleep(0.2)
        print("Hand Capture Thread stopped successfully.")

    def draw(self, display):
        if self.success and self.active and self.pg_srf is not None:
            srf_rect = self.pg_srf.get_rect()
            srf_rect.top = 0
            srf_rect.right = self.engine.width
            display.blit(self.pg_srf, srf_rect)

    def terminate(self):
        if self.capture_thread.is_alive():
            self.capture_thread.join()

        self.capture.release()
        cv2.destroyAllWindows()
        print("OpenCV and MediaPipe terminated successfully.")



class JoyStick:

    def __init__(self):

        self.joystick = None

        if pg.joystick.get_count() > 0:
            self.joystick = pg.joystick.Joystick(0)
            self.joystick.init()
            self.success = True

            print("Joystick init successful!")
            print(f"Joystick Name: {self.joystick.get_name()}")
            print(f"Number of Axes: {self.joystick.get_numaxes()}")
            print(f"Number of Buttons: {self.joystick.get_numbuttons()}")

        self.valid_events = js.VALID_JOYSTICK_EVENTS

        # As submarine controls, we have 'TRUST', 'SPRAY' and 'BALLAST'
        self._thrust_on = False
        self._spray_on = False
        self._thrust_force = 0  # -1, 0, 1
        self._spray_force = 0  # -1, 0, 1
        self._ballast_fill = 50  # 0, 50, 100

        # As map controls we have 'SCROLL left/right/top/bottom' and 'AUTOSCROLL'
        # scroll direction is changed from -1 to 1
        self.autoscroll_on = False
        self.autoscroll_pressed = False
        self.scroll_direction = (0, 0)


    def get_joystick_data(self):

        if self._thrust_on:
            thrust_force = self._thrust_force
            if thrust_force == 0:
                engine_mode = "engine-off"
            else:
                engine_mode = "engine-on"
        else:
            thrust_force = 0
            engine_mode = "engine-off"


        if self._spray_on:
            spray_force = self._spray_force
            if spray_force > 0:
                spray_mode = "top-spray"
            elif spray_force < 0:
                spray_mode = "btm-spray"
            else:
                spray_mode = "no-spray"
        else:
            spray_force = 0
            spray_mode = "no-spray"

        return engine_mode, spray_mode, thrust_force, spray_force, self._ballast_fill

    def get_thruster_state(self):
        return self._thrust_on

    def get_spray_state(self):
        return self._spray_on

    def event_decode(self, event):
        """ Check and decode the joystick controls.
            Note: Instead of using 'pygame.JOYBUTTONDOWN' and pygame.JOYAXISMOTION, we check the event type raw value.
        """
        # -- MAP-SCROLL ---:
        if event.type == js.MAP_SCROLL_SWITCH:
            if event.value:
                self.scroll_direction = (event.value[0], -event.value[1])
            else:
                self.scroll_direction = (0, 0)
                # Note: For y axis the direction calculation is inverted.
                # This is why we change the sign of the joystick direction

        # -- THRUSTTER AND SPRAY ON/OFF ---
        if event.type == js.BTN_DOWN_EVENT:
            # When button is DOWN:
            if event.button == js.THRUST_BTN:
                self._thrust_on = True
                self._spray_on = True

            elif event.button == js.AUTOSCROLL_BTN:
                self.autoscroll_pressed = True

            # using another button for spray-on, instead:
            # if event.button == 2:
            #     self._spray_on = True

        elif event.type == js.BTN_UP_EVENT:
            # When button is UP:
            if event.button == js.THRUST_BTN:
                self._thrust_on = False
                self._spray_on = False
                # self.change_thrust_force(0)

            elif event.button == js.AUTOSCROLL_BTN and self.autoscroll_pressed:
                self.autoscroll_on = not self.autoscroll_on
                print(f"Autoscroll: {self.autoscroll_on}")
                self.autoscroll_pressed = False

            # using another button for spray-on, instead:
            # if event.button == 2:
            #     self._spray_on = False

        # -- THRUST and SPRAY values, from axis-control position:
        if event.type == js.AXIS_CHANGE_EVENT:
            if event.axis == js.AXIS_X:  # axis id's returned from pygame.event
                # self._spray_force = self.change_spray_force(event.value)
                self._spray_force = -event.value

            elif event.axis == js.AXIS_Y:
                # self._thrust_force = self.change_thrust_force(event.value)
                self._thrust_force = -event.value

            elif event.axis == js.AXIS_BALLAST:
                self._ballast_fill = self.change_ballast_fill(event.value)

    @staticmethod
    def change_thrust_force(event_value):
        # Note: event_value is float, between -1 and 1
        # This method scale the value to another min-max
        min_thrust = -20  # px/frame
        max_thrust = 20

        if event_value == 0:
            return 0
        else:
            inverted_value = -1 * event_value  # Inverting the direction of the joystic control

            output_value = Tools.range_value(inverted_value, -1.0, 1.0, min_thrust, max_thrust)
            # The output value for thrust force will be ranged between -20 and 20 px/frame
            return output_value

    @staticmethod
    def change_spray_force(event_value):
        # Note: event_value is float between -1 and 1
        # This method change the value to another min-max
        min_spray = -5
        max_spray = 5

        if event_value == 0:
            return 0
        else:
            inverted_value = -1 * event_value
            output_value = Tools.range_value(inverted_value, -1.0, 1.0, min_spray, max_spray)
            return output_value

    @staticmethod
    def change_ballast_fill(event_value):
        # Note: Event_value is float between -1 and 1.
        min_ballast = 0
        max_ballast = 100

        if event_value == 0:
            return 50
        else:
            inverted_value = -1 * event_value
            output_value = Tools.range_value(inverted_value, -1.0, 1.0, min_ballast, max_ballast)
            output_value = int(output_value)
            return output_value


# class Mouse:
#     def __init__(self, endine):
#         # self.pos = (0, 0)
#         self.engine = endine
#         self.event = None
#
#     def left_down(self, pos):
#         self.event = {"left-down":pos}
#
#     def left_up(self, pos):
#         self.event = {"left-up": pos}
#
#     def right_down(self, pos):
#         self.event = {"left-up": pos}
#
#     def right_up(self, pos):
#         ...
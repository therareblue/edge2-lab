# from pygame import Surface, image as pgimage, SRCALPHA
import pygame as pg
import os
import json


class ColorPalette:
    # -- Uni: --
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (106, 190, 48)
    YELLOW = (251, 242, 54)

    # -- SUB: --
    # -> Sub is using BLACK, WHITE and RED.

    # -- WATER: --
    SHALLOW = (125, 178, 193)
    DEEP = (81, 121, 201)
    TRENCH = ()

    SKY_BLUE = (135, 206, 235)
    DARK_BLUE = (0, 0, 139)
    SILVER = (105, 106, 106)


    @staticmethod
    def transparent_fill(color, alpha):
        return color + (alpha,)


# --- SCREEN SETTINGS ---
class ScreenSettings:

    MONITOR_DEFAULT = (1920, 1080)
    SCALE_FACTOR = 1.5  # The monitor resolution is scaled-down to 1.5
    SCROLL_SPEED = 10  # Scroll at speed 10 px/frame
    FPS = 60


# --- MAP ---
class MapSettings:

    CELL_SIZE = 32
    # Note: Each element is a rectangle, with size of CELL_SIZE

    # TILES_X = 300  # Number of tiles on X-Axis
    # TILES_Y = 330  # Number of tiles on Y-Axis

    CELLS_X = 300
    CELLS_Y = 350


class FileLocations:
    CELL_IMAGES = "img/map/"
    BIO_IMAGES = "img/bio/"
    WATER_IMAGES = "img/water/"
    EDITOR_IMAGES = "img/editor/"

    CLEAR_CELL = "img/map/map-none.png"

    SUB_IMAGES = "img/sub/"

    # Types of images. Used when loading the image libraries
    #     to separate them into this key_features
    CELLULAR_TYPES = ["map-rock", "lava-rock", "lava-water"]
    BIOLIFE_TYPES = ["bush"]


# --- JOYSTICK ---
class JoystickSettings:
    VALID_JOYSTICK_EVENTS = [1536, 1538, 1539, 1540]

    BTN_DOWN_EVENT = 1539
    BTN_UP_EVENT = 1540

    THRUST_BTN = 0  # bottom-center-button
    SPRAY_BTN = 2  # bottom-right button
    AUTOSCROLL_BTN = 1  # Top-center button

    MAP_SCROLL_SWITCH = 1538
    # Note: this switch causes a tuple (0,0)/(1,1)(-1,-1) for the four positions. When All-buttons-up, value = (0,0)

    AXIS_CHANGE_EVENT = 1536
    AXIS_X = 0  # used for spray
    AXIS_Y = 1  # used for main thruster
    AXIS_BALLAST = 2


class KeyboardSettings:
    ...


class HandShakeSettings:
    """ Keeps all settings for hand sign recognizer """
    ...


# Note for Img loading:
# in the json file there is img-id,
# telling which is the image file for the each props.


class EnvironmentProps:
    SEAWATER_SHALLOW = {
        "id": 0,
        "color": ColorPalette.SHALLOW,
        "deep": 400,
        "depth": 400,
        "resistance": 3,
        "temp": 19,
        "max-temp": 25,
        "min-temp": 15
    }

    SEAWATER_DEEP = {
        "id": 1,
        "color": ColorPalette.DEEP,
        "deep": 800,
        "depth": None,
        "resistance": 3,
        "temp": 8,
        "max-temp": 15,
        "min-temp": 4
    }


class SubSettings:
    PHYSICS_CHECK_RANGE = (12, 12)
    MAX_VELOCITY = 5  # pixels per frame

    MASS = 20
    # Note: The mass of the vessel affect the acceleration (building of momentum) when a force is applied.

    # RESOLUTION: pixels of movement prf frame
    BUOYANCY_RESOLUTION = 1
    SPEED_RESOLUTION = 5
    ROTATION_RESOLUTION = 1

    INIT_DEPTH = 150

    INIT_ENERGY = 0.4
    INIT_INTEGRITY = 1


class VisionSettings:
    VISION_COLS = 16,
    VISION_ROWS = 16









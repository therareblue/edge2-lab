import pygame as pg
from typing import List
from settings import MapSettings

# import tensor as tf


class VisionLaser:
    def __init__(self, engine, max_range:int, vision_angle:float):
        self.engine = engine
        # 'engine' reff. is used to obtain all the information (from bio and map) on the way of the laser.

        self.range = max_range
        self.angle = vision_angle


class Senses:
    """ The module aims to collect information from Physics and Health module.
        It is not used for physical appearance or health change.
        It only for the brain (decision-making)
    """
    LASER_RANGE = 500  # laser max length in pixels

    def __init__(self, unit):
        self.unit = unit
        # from unit we use shared params only:
        # heading,

        self.engine = unit.engine

        # --- Internal ---
        self.integrity = None
        self.temp_in = None
        self.pressure_in = None


        # --- External ---
        self.temp_out = None
        self.pressure_out = None

        # Initializing the vision sensor.
        # For the demo we use 1 laser sensor on front. Later, here will be several on each side of the unit.
        laser_angle = 0
        vision_laser = VisionLaser(
            engine=self.engine,
            max_range=self.LASER_RANGE,
            vision_angle=laser_angle
        )


    def update(self):
        """
            1. We need to detect the life_unit or the cell_id (row, col), where the laser first hits.
            2. Get all the data from this unit.

        """
        # --> 1. Get the heading:
        heading = self.unit.heading

        ...


# ================== VISION USING CELL-MATRIX ==================
# TODO: More detailed vision will be with celular matrix in some range.
# Then, every cell will be a Convolution-Network neuron with few dimensions for each cell property.

class VisionPixel:
    def __init__(self, cell_mask, cell_props:dict, population:list):
        """ A pixel representing 1 cell of the vision, with MapSettings.CELL_SIZE;
            Used to store information from the cell that is in the range of Vision.
        """
        self.cell_mask = None
        self.cell_props = None

    def get_props(self):
        result = ()
        # TODO: return the pixel data only needed for the Vision Neural Network
        ...
        return result


class VisionCamera:
    def __init__(self, engine, vision_range: tuple, sub_center: tuple):
        """ Creates a 'moment of vision' in cells, that has cell data,
            from given center of submarine and vision_range (cols, rows)
        """
        self.engine = engine

        self.range = vision_range
        self.cols, self.rows = range

        self.sub_center = sub_center

        # Property:
        # self.pixels = []  # a list of cells with various cell data in it.

        # TODO: when changing sub_center, the population of VisionPixels is changed.
        ...

    @property
    def pixels(self):
        result = []
        # TODO return a list of VisionPixel elements, keeping the data of the cells arround the sub center.
        # Note: If the sub_center is changed, calling this will get different list of cells.

        # 1. Calculate the index of the cell, where the sub_center is
        ...
        # 2. Get the indexes for top-left cell and bottom-right cell
        ...
        # 3. Loop over the indexes and collect information, creating VisionPixel instances
        ...
        # 4. Populate the 'result' list and return it.
        ...
        return result


class VisionBrain:
    def __init__(self):
        ...


class Vision:
    def __init__(self, engine, camera_range:tuple):
        self.engine = engine

        self.range = camera_range

        submarine_center = (self.engine.sub.pos_x, self.engine.sub.pos_y)
        self.camera = VisionCamera(engine=engine,
                                   vision_range=camera_range,
                                   sub_center=submarine_center)

        ...


# ======================== HAND RECOGNIZER ========================
# TODO:
"""
Build a simple Hand signs clasifier, 
capable to recognize the command from the moving hand. 
Each point of the hand is a neuron with coordinates (x, y)
"""


# =========================== BRAIN ===============================

class DecisionMaking:
    ...


# TODO: the brain class combines both vision and decision_making.
#  It slso ensures that only one instance of Vision and DecisionMaking classes are created

class SubBrain:
    ...


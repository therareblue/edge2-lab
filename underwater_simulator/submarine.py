import pygame as pg

import math

from settings import ColorPalette as clr

from typing import List

from settings import VisionSettings, SubSettings
# from physics import ImpactMedium, Physics
from physics import Physics, UnitHealth

from tools import Tools

# from brain import Vision

# sudo pip3 install --upgrade evdev
# works only on linux OS


# TODO: remove AnimationSheet class and use the Animation class from settings.py
class AnimationSheet:
    def __init__(self, img_src: str, sprite_size: tuple, number_of_frames: int):
        self.sheet = pg.image.load(img_src).convert()
        self.sheet.set_colorkey(clr.WHITE)

        self.width = sprite_size[0]
        self.height = sprite_size[1]
        self.number_of_frames = number_of_frames

        self.frames_list = []
        self.fill_img_list()

    def get_image(self, frame=0, scale=1, color=clr.BLACK):
        # -- Create an empty surface with the size of 'sprite_size':
        image = pg.Surface((self.width, self.height))
        # paste a portion from the sheet inside the created surface:
        # image.fill(clr.WHITE)
        image.blit(self.sheet, (0, 0), ((frame * self.width), 0, self.width, self.height))
        image.convert()
        image.set_colorkey(clr.WHITE)

        if scale > 1:
            image = pg.transform.scale(image, (self.width * scale, self.height * scale))
        image.set_colorkey(color)

        return image

    def fill_img_list(self):
        for f in range(self.number_of_frames):
            img = self.get_image(frame=f)
            self.frames_list.append(img)


class Sub20:
    WIDTH = 350
    HEIGHT = 150

    ANIMATION_FRAMES = 5

    ENGINE_MODES = ["engine-off", "engine-on"]
    SPRAY_MODES = ["no-spray", "top-spray", "btm-spray"]

    def __init__(self, engine):
        self.engine = engine

        self.settings = SubSettings

        # self.width = self.WIDTH
        # self.height = self.HEIGHT

        # Position the center coordinates of the sub to the center of the screen (-200px on y)
        self.init_position = (self.engine.width // 2, (self.engine.height // 2) + self.settings.INIT_DEPTH)
        self.pos_x, self.pos_y = self.init_position

        # --- ANIMATION ---
        self.scene = {
            "engine-off": {
                "no-spray": AnimationSheet('img/sub/sub_sheet_off_no_sprite.png', (self.WIDTH, self.HEIGHT), self.ANIMATION_FRAMES),
                "top-spray": AnimationSheet('img/sub/sub_sheet_off_top_sprite.png', (self.WIDTH, self.HEIGHT), self.ANIMATION_FRAMES),
                "btm-spray": AnimationSheet('img/sub/sub_sheet_off_btm_sprite.png', (self.WIDTH, self.HEIGHT), self.ANIMATION_FRAMES),
            },
            "engine-on": {
                "no-spray": AnimationSheet('img/sub/sub_sheet_on_no_sprite.png', (self.WIDTH, self.HEIGHT), self.ANIMATION_FRAMES),
                "top-spray": AnimationSheet('img/sub/sub_sheet_on_top_sprite.png', (self.WIDTH, self.HEIGHT), self.ANIMATION_FRAMES),
                "btm-spray": AnimationSheet('img/sub/sub_sheet_on_btm_sprite.png', (self.WIDTH, self.HEIGHT), self.ANIMATION_FRAMES),
            },
        }

        self.size = (self.WIDTH, self.HEIGHT)

        # Note: Changing this will change the rendered image (see the self.scene):
        self.engine_mode = self.ENGINE_MODES[0]
        self.spray_mode = self.SPRAY_MODES[0]

        # main-image load:
        self.frame_index = 0
        self.image = self.scene[self.engine_mode][self.spray_mode].frames_list[self.frame_index].copy()
        # Note: Copying the frame used assure the original will last unchanged.
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_x, self.pos_y)  # Position the center of the sub on pos_x and pos_y coords

        # Loading the contour image, outlining the sub's body only, without the effects.
        # Used for collision detection.
        self.contour_image_original = pg.image.load("img/sub/sub_shadow.png").convert()
        self.contour_image_original.set_colorkey(clr.WHITE)

        # Calculating the surface area, used in overlapping (see physics, is_underwater() method)
        # x, y = self.contour_image_original.get_size()
        # self.contour_area = x * y * 0.5  # The covered area is ruffly 50% of the image.
        self.contour_area = Tools.get_image_acrive_pixels_area(self.contour_image_original)

        # self.contour_image = self.contour_image_original.copy()
        # self.contour_rect = self.contour_image.get_rect()
        # self.contour_rect.center = self.rect.center
        #
        # # Collision mask:
        # self.mask = pg.mask.from_surface(self.contour_image)

        # animation-speed:
        # Note: animation speed is changed regarding the movement speed of the sub...
        self.animation_speed = 100
        self.last_frame_update = pg.time.get_ticks()

        # --- controllers get_data interval ---
        self.control_check_interval = 100
        self.last_control = pg.time.get_ticks()  # last time check for keyboard
        self.last_joystick = pg.time.get_ticks()  # last time check for joystick event
        # -----------------

        # --- SUB STATE ---
        self.thrust_force = 0  # -1 to +1
        self.spray_force = 0  # -1 to +1
        self.ballast_fill = 50  # 50% is the fill for buoyancy = 0

        self.heading = 0  # from 0 to 359 degrees, counter_clockwise!
        # Note: heading is a float, representing angle of rotation of the object;
        # Because the pygame.transform.rotate, rotates counter-clockwise,
        # the angle is measured from 0, corresponding to axis_x, counter-clockwise

        # --- COLLISION ---
        # Create a circular mask in the center of the submarine, for sensing and floating purposes
        center_mask_radius = 5
        center_mask_srf = pg.Surface((center_mask_radius * 2, center_mask_radius * 2))
        center_mask_srf.fill(clr.BLACK)
        pg.draw.circle(center_mask_srf, clr.WHITE, (center_mask_radius, center_mask_radius), center_mask_radius)
        center_mask_srf.convert()
        center_mask_srf.set_colorkey(clr.BLACK)
        self.center_mask = pg.mask.from_surface(center_mask_srf)
        # self.center_rect = center_mask_srf.get_rect()
        # self.center_rect.center = (self.pos_x, self.pos_y)

        self.next_img = None
        self.next_img_pos = (0, 0)
        self.next_img_mask = None

        # --- PHYSICS ---
        self.physics = Physics(self)
        self.mean_force = 0  # Used in interface gauger

        # --- HEALTH ---
        # TODO: Put this in a shared Healt class...
        self.health = UnitHealth(
            unit=self,
            init_energy=SubSettings.INIT_ENERGY,
            init_integrity=SubSettings.INIT_INTEGRITY
        )

        # --- NEURAL ---
        self.ai_active = False
        self.senses = Senses(self, )


    @property
    def center_cell_coords(self):
        """ Get the coordinates of the cell, located on the sub center (pos_x and pos_y)...
        """
        # sub_center_coords = (self.rect.center[0] + self.engine.scroll_x, self.rect.center[1] + self.engine.scroll_y)
        center_cell_index_x = int(self.pos_x // self.engine.image_library.cell_size)
        center_cell_index_y = int(self.pos_y // self.engine.image_library.cell_size)

        return center_cell_index_x, center_cell_index_y

    @property
    def buoyancy(self):
        """returns the buoyancy in range: -1, 0 +1
        """
        ballast_effect = 2*(50 - self.ballast_fill) / 100  # on ballast_fill=100%, effect = -1; when 50%: effect=0
        buoyancy = ballast_effect + self.health.structural_buoyancy
        return buoyancy

    @property
    def effect_of_resistance(self):
        passable_resistance_effect = self.physics.calculate_resistance_effect(self.thrust_force, self.spray_force)
        nonpassable_resistance_effect = self.physics.calculate_resistance_effect(self.thrust_force, self.spray_force, "non-passable")
        return (abs(passable_resistance_effect), abs(nonpassable_resistance_effect))


    # @property
    # def engine_mode(self):
    #     return self._engine_mode
    #
    # @engine_mode.setter
    # def engine_mode(self, value:str):
    #     if value in self.ENGINE_MODES:
    #         self._engine_mode = value
    #     else:
    #         raise ValueError("Valid modes are: engine-off, engine-on")


    # @property
    # def get_scaled_buoyancy(self):
    #     """Converts the buoyancy into pixels-per-frame movement...
    #     """
    #     converted_buoyancy = int(self.buoyancy * self.BUOYANCY_SCALE_FACTOR)
    #     return converted_buoyancy

    # TODO: An option of getting the thrust_force and spray_force is to use a property,
    # TODO: that gets the value from th joystick / brain (if Ai driven)

    # @property
    # def thrust_force(self):
    #     thrust_force = 0
    #     # -check for joystick control:
    #     if not self.ai_active:
    #         if self.engine.joystick.success:
    #             if self.engine.joystick.get_thruster_state():
    #                 thrust_force = self.engine.joystick.get_thrust_force()
    #                 if self.thrust_force == 0:
    #                     self.engine_mode = "engine-off"
    #                 else:
    #                     self.engine_mode = "engine-on"
    #             else:
    #                 thrust_force = 0
    #                 self.engine_mode = "engine-off"
    #
    #     return thrust_force


    def get_joystick(self):
        time_now = pg.time.get_ticks()
        if time_now - self.last_joystick > self.control_check_interval:
            self.engine_mode, self.spray_mode, self.thrust_force, self.spray_force, self.ballast_fill = self.engine.joystick.get_joystick_data()

            if self.health.battery_empty:
                self.spray_force = 0
                self.thrust_force = 0

            self.last_joystick = time_now

    def check_controllers(self):
        if self.engine.joystick.success:
            self.get_joystick()

        else:
            # TODO: check for keyboard controls instead...
            ...

    def get_next_heading(self):
        next_heading = self.heading + self.physics.rotation_momentum
        if next_heading > 360:
            next_heading -= 360.0
        elif next_heading < 0:
            next_heading += 360.0

        return next_heading

    @staticmethod
    def calculate_new_coordinates(init_coordinates: tuple, direction: float, distance):
        """Calculating coordinates (x2, y2) from given point (x1, y1), length and angle from axis X"""
        # Note: self.velocity (px/frame) is used for the distance need to be moved:

        angle_rad = math.radians(-direction)
        # Calculate the change in x and y coordinates:
        delta_x = distance * math.cos(angle_rad)
        delta_y = distance * math.sin(angle_rad)

        new_x = init_coordinates[0] + int(delta_x)
        new_y = init_coordinates[1] + int(delta_y)

        return new_x, new_y

    # @staticmethod
    # def resistance_heading(center, point1, point2):
    #     """Calculates the angle between two lines (center to point1, center to point2)...
    #     """
    #     vector1 = (point1[0] - center[0], point1[1] - center[1])
    #     vector2 = (point2[0] - center[0], point2[1] - center[1])
    #
    #     angle = math.atan2(vector2[1], vector2[0]) - math.atan2(vector1[1], vector1[0])
    #     angle = math.degrees(angle)
    #
    #     if angle < 0:
    #         angle += 360
    #
    #     return angle

    def move(self):

        next_heading = self.get_next_heading()
        next_pos_x, next_pos_y = self.calculate_new_coordinates(
            (self.pos_x, self.pos_y),
            next_heading,
            self.physics.velocity
        )

        # next_pos_y -= self.buoyancy_momentum
        # NOTE: When the buoyancy is opposite the thrust-force and there will be collision, it blocks the movement.
        # This "if" partly fixing the problem:
        if abs(self.physics.velocity) <= abs(self.physics.buoyancy_momentum):
            next_pos_y -= self.physics.buoyancy_momentum

        # Apply the impact from the surrounding medium. This will affect sub's health and will return new positions.
        self.physics.apply(
            next_pos=(next_pos_x, next_pos_y),
            next_heading=next_heading
        )

    def reset_position(self):
        self.pos_x, self.pos_y = self.init_position
        self.heading = 0


    def update(self):

        self.check_controllers()

        self.physics.update(
            thrust_force=self.thrust_force,
            spray_force=self.spray_force,
            buoyancy=self.buoyancy
        )
        self.move()

        # --- animation ---
        time_now = pg.time.get_ticks()
        if time_now - self.last_frame_update > self.animation_speed:
            # --- get the right frame:
            self.image = self.scene[self.engine_mode][self.spray_mode].frames_list[self.frame_index].copy()
            self.rect = self.image.get_rect()

            # --- rotation:
            if not self.heading == 0:
                self.image = pg.transform.rotate(self.image, self.heading)
                self.rect = self.image.get_rect()

            # --prepare the frame index for the next frame update:
            if self.frame_index >= self.ANIMATION_FRAMES - 1:
                self.frame_index = 0
            else:
                self.frame_index += 1

            self.last_frame_update = time_now

        # TODO: The submarine will start from certain position, and will float on the water surface.
        # --- positioning ---
        self.rect.center = (self.pos_x - self.engine.scroll_x, self.pos_y - self.engine.scroll_y)
        # self.rect.center = (self.pos_x, self.pos_y)

        # --= Updating health ---
        sub_depth = self.physics.depth_from_pixels(self.pos_y)
        pressure_out = self.physics.pressure_from_depth(sub_depth)
        water_temperature = self.physics.surrounding_temp

        total_energy_in = self.physics.solar_energy + self.physics.thermal_energy

        self.health.update(
            temp_out=water_temperature,
            pressure_out=pressure_out,
            thrust_force=self.thrust_force,
            spray_force=self.spray_force,
            energy_in=total_energy_in

        )

    def draw(self):
        self.engine.display.blit(self.image, self.rect)
        self.physics.draw_impact()































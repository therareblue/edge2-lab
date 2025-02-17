# import sys
# import time
# import psutil

import os

# from pygame import font, draw, time as pgtime
import pygame as pg

import math

from settings import MapSettings, ColorPalette as clr
from tools import Tools


class Pointer:
    """Pointer is an information interface that extracts and shows
        the object data ('props') where the pointer mask is located.

        It works both with mouse move and with hand gesture recognizer (see 'controllers.py' module)
    """
    SIZE = (10, 10)
    BASE_COLOR = clr.WHITE
    COLLISION_COLOR = clr.RED

    INFOBOX_SIZE = (150, 100)
    # INFOBOX_COLOR_ALPHA = clr.BLACK
    INFOBOX_FONT_COLOR = clr.BLACK
    INFOBOX_FONT_SIZE = 10
    INFOBOX_OFFSET = (20, -10)  # This is the topleft relative to mouse pointer

    def __init__(self, engine):
        self.engine = engine


        # self.pos_x, self.pos_y = (0, 0)
        self._position = pg.mouse.get_pos()

        self._active = False

        self.color = self.BASE_COLOR

        self.pointer_surface = pg.surface.Surface(self.SIZE)
        self.pointer_rect = self.pointer_surface.get_rect()
        self.pointer_rect.center = self.position
        self.pointer_mask = pg.mask.from_surface(self.pointer_surface)

        # self.infobox = pg.surface.Surface(self.INFOBOX_SIZE)
        # self.infobox.convert()
        # self.infobox.set_colorkey(self.INFOBOX_COLOR_ALPHA)
        # Note: If the surface is not filled with white alpha color, it will remain black.
        # Then when converting, the color_key should be set to black, for transparancy.
        # self.infobox_rect = self.infobox.get_rect()

        self.infobox_font = pg.font.Font("freesansbold.ttf", self.INFOBOX_FONT_SIZE)
        self.text_lines = ["Welcome to subColony..."]

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value: tuple):
        self._position = value
        if self.pointer_rect is not None:
            self.pointer_rect.center = value

    @property
    def infobox_position(self):
        pos_x = self._position[0] + self.INFOBOX_OFFSET[0]
        pos_y = self._position[1] + self.INFOBOX_OFFSET[1]
        return pos_x, pos_y

    @property
    def position_on_map(self):
        pos_x = int(self._position[0] + self.engine.scroll_x)
        pos_y = int(self._position[1] + self.engine.scroll_y)
        return pos_x, pos_y

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value:bool):
        self.position = pg.mouse.get_pos()
        self._active = value

    def check_collision(self):
        """ Based on pointer map-coordinates,
        method returns list of objects props, colided with
        """
        # BIG-NOTE: CHECK FOR MASK OVERLAP only with water masks.
        # For other objects, just EXTRACT UNITS INFORMATION, BASED ON THE POINTER COORDINATES ON THE MAP.

        collision_data = {
            "water-data": None,     # only one water type can be located at the pointer position.
            "map": None,  # collision with only one map-cell can appear
            "biolife-data": []  # If multiply life forms located on the position, pointer returns all their data.

            # Note: If more unit types are created in future, they should be added here.
        }
        # TODO: --> Check collision with water
        ...

        # --> Check collision with Cells object (map)
        # 1. Calculate the index of the cell, located on the center of pointer
        center_cell_index_x = int(self.position_on_map[0] // self.engine.image_library.cell_size)
        center_cell_index_y = int(self.position_on_map[1] // self.engine.image_library.cell_size)
        index_str = f"row={center_cell_index_y} | cell={center_cell_index_x}"

        # 2. Get the cell data:
        # cell_data_index = self.engine.map.map_structure[center_cell_index_y][center_cell_index_x]
        row_index = center_cell_index_y
        cell_index = center_cell_index_x
        cell_description = self.engine.map.get_cell_property((cell_index, row_index), "description")
        cell_props = self.engine.map.get_cell_property((cell_index, row_index), "props")
        cell_biolist = self.engine.map.map_structure[row_index][cell_index]
        map_cell_data = {
            "description": cell_description,
            "position": index_str,
            "props": cell_props,
            "struct":cell_biolist
        }
        collision_data["map"] = map_cell_data

        ...

        # --> Check collision with biolife objects:
        # 1. Get biolife mask if any life on that coordinates were found..
        #   If found, return its mask and center position
        # found_units_id = self.engine.biolife.unit_id_list_from_coordinates(self.position_on_map)

        # list of unit_id, found in this cell
        found_units_id = self.engine.map.map_structure[row_index][cell_index][3]

        found_life_info = [self.engine.biolife.get_unit_info(unit_id) for unit_id in found_units_id]
        for unit_info in found_life_info:
            collision_data["biolife-data"].append(unit_info)

        return collision_data

    def update(self):
        if self.active:
            # Get the position:
            self.position = pg.mouse.get_pos()

            # Check for objects data on that position (collision detection of pointer with others)

            collision_data = self.check_collision()

            self.text_lines = self.generate_text_lines(collision_data)


            # TODO: add an option to change the position based on hand-finger recognition (camera and mediapipe)

            # TODO: Automaticaly resize the infobox panel based on width of lines and their number.
            ...

    def draw_pointer(self):
        """ Method to draw a small collored rectangle on the """
        self.pointer_surface.fill(self.color)
        self.engine.display.blit(self.pointer_surface, self.pointer_rect)

    def generate_text_lines(self, collided_objects_data):
        # Format:
        # collided_objects_data = {
        #     "water-data": ...,
        #     "map-cell-data": ...,
        #     "biolife-data": [..., ..., ...]
        # }
        tab = "    "
        lines = [
            f"Coordinates: x={self.position_on_map[0]} | y={self.position_on_map[1]}",
            f"{tab}"
        ]
        if collided_objects_data['water-data'] is not None:
            lines.append(f"Water: T={collided_objects_data['water-data']['temp']:.2f}, P={0}")
        else:
            lines.append(f"Water: T = 0 | P = 0 bar")

        lines.append(f"Map: {collided_objects_data['map']['description']}")
        lines.append(f"{tab}Position: {collided_objects_data['map']['position']}")

        for key, value in collided_objects_data['map']["props"].items():
            lines.append(f"{tab}{str(key).capitalize()}: {value}")

        lines.append(f"Structure: {collided_objects_data['map']['struct']}")

        for i, obj_data in enumerate(collided_objects_data["biolife-data"]):
            lines.append(f"Unit {i+1}: {obj_data['description']}")
            # print(obj_data["props"])

            for key, value in obj_data["props"].items():
                lines.append(f"{tab}{str(key).capitalize()}: {value}")

        return lines


    def draw_infobox(self):

        # perc = int(self.engine_data['thrust'] * 100)
        # t_string = f"{perc}%"
        # srf = font.render(t_string, True, clr.WHITE)
        # rc = srf.get_rect()
        # rc.center = t_end
        # self.engine.display.blit(srf, rc)

        # 2. Set the first line position:
        y_offset = 0

        # 3. draw all lines:
        for line in self.text_lines:
            rendered_text = self.infobox_font.render(line, True, self.INFOBOX_FONT_COLOR)
            self.engine.display.blit(rendered_text, (self.infobox_position[0], self.infobox_position[1]+y_offset))
            y_offset += self.INFOBOX_FONT_SIZE

        ...

    def draw(self):
        # Drawing a rectangular pointer 10x10px on the screen, when is active
        if self.active:
            self.draw_pointer()
            self.draw_infobox()

""" TODO:
    Pointer will be activated and deactivated via K_p button. 
    While moving, an info box will be moving with it 
"""

class Gauger:

    def __init__(self, engine):
        self.engine = engine

        self.center_x = 50
        self.center_y = self.engine.height // 2

        self.color = clr.WHITE

        self.data = {}

        self.depth = {
            "min": 0,
            "max": 0,
            "current": self.depth_from_pixels(self.engine.sub.pos_y)
        }
        self.water_props = {
            "pressure": self.pressure_from_depth(self.depth['current']),
            "temp": 0
        }

        self.engine_data = {
            "thrust": 0,
            "spray": 0,
            "ballast": 50,
            "buoyancy": 0,
        }

        self.physics_data = {
            "resistance": (0, 0),  # (passable, non_passable)
            "force": 0
        }

        self.health_data = {
            "integrity": 0,
            "charge": 0
        }

        self.full_depth = self.depth_from_pixels(self.engine.map.cells_y * self.engine.map.cell_size)

        self.battery_sheet = self.load_battery_sheet()
        self.font_10 = pg.font.Font("freesansbold.ttf", 10)

        time_now = pg.time.get_ticks()
        # for up to 3 warning signs
        self.last_warning_blink = [time_now, time_now, time_now]

        # heading gauge:
        gauge_img = pg.image.load("img/interface/sub-gauge-0.png").convert()
        sub_img = pg.image.load("img/interface/sub-gauge-1.png").convert()
        gauge_img.set_colorkey(clr.BLACK)
        sub_img.set_colorkey(clr.BLACK)
        self.heading_gauge_images = {
            "gauge": gauge_img,
            "sub": sub_img
        }

        self.warning_img = pg.image.load("img/interface/warning-sign.png").convert()
        self.warning_img.set_colorkey(clr.BLACK)

    @staticmethod
    def depth_from_pixels(pixels):
        """Get pixels (the y position) and converts it to a depth value"""

        # Note: 100 px = 10m
        depth = (pixels / 10) - 40
        if depth < 0:
            depth = 0
        return depth

    @staticmethod
    def pressure_from_depth(depth):
        pressure = 1 + depth / 10
        return pressure

    def update(self):
        # Get the information of the submarine

        # external_temp_water = self.engine.sub.physics.water_temp_from_pixels(self.engine.sub.pos_y)
        # external_temp_cells = self.engine.sub.physics.total_cells_temp
        # total_temp = (external_temp_water + external_temp_cells) / 2

        self.depth = {
            "top": self.depth_from_pixels(self.engine.scroll_y),
            "btm": self.depth_from_pixels(self.engine.scroll_y + self.engine.height),
            "current": self.depth_from_pixels(self.engine.sub.pos_y)
        }
        self.water_props = {
            "pressure": self.pressure_from_depth(self.depth['current']),
            # "temp": total_temp,
            "temp": self.engine.sub.physics.surrounding_temp,
            # TODO: change the water-temp with total calculated temp from the collisions and water, in module physics.
            "resistance": 0
        }

        self.engine_data = {
            "thrust": self.engine.sub.thrust_force,
            "spray": self.engine.sub.spray_force,
            "ballast": self.engine.sub.ballast_fill,
            "buoyancy": self.engine.sub.buoyancy
        }

        self.physics_data = {
            # "resistance": (abs(self.engine.sub.resistance_affect_passable), abs(self.engine.sub.resistance_affect_nonpassable)),
            "resistance": self.engine.sub.effect_of_resistance,
            "force": self.engine.sub.mean_force
        }

        self.health_data = {
            "integrity": 0,
            "charge": 0,
            "dps": self.engine.sub.health.damage_rate
        }

    def draw_resistance_gauge(self):
        start_point = (self.center_x+145, self.center_y+90)
        bars_distance = 25
        bar_width = 10
        third_distance = start_point[0] + bars_distance + bar_width + bars_distance+5
        total_width = 2*bar_width + bars_distance

        font = self.font_10
        t_string = "RESISTANCE"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = (start_point[0]+bars_distance//2, start_point[1] + 12)
        self.engine.display.blit(srf, rc)

        t_string = "FORCE"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = (third_distance, start_point[1] + 12)
        self.engine.display.blit(srf, rc)

        bar_len = 180
        resistance_passable_bar = bar_len * self.physics_data["resistance"][0]
        resistance_nonpassable_bar = bar_len * self.physics_data["resistance"][1]
        force_bar = bar_len * self.physics_data["force"]

        t_start = (start_point[0], start_point[1])
        t_end = (start_point[0], start_point[1]-resistance_passable_bar)
        pg.draw.line(self.engine.display, clr.BLUE, t_start, t_end, bar_width)

        font = self.font_10
        val = self.physics_data['resistance'][0]
        t_string = f"{val:.2f}"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = t_end
        rc.bottom = t_end[1] - 5
        self.engine.display.blit(srf, rc)

        t_start = (start_point[0]+bars_distance, start_point[1])
        t_end = (start_point[0]+bars_distance, start_point[1] - resistance_nonpassable_bar)
        pg.draw.line(self.engine.display, clr.RED, t_start, t_end, bar_width)

        val = self.physics_data['resistance'][1]
        t_string = f"{val:.2f}"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = t_end
        rc.bottom = t_end[1] - 5
        self.engine.display.blit(srf, rc)

        t_start = (third_distance, start_point[1])
        t_end = (third_distance, start_point[1] - force_bar)
        pg.draw.line(self.engine.display, clr.WHITE, t_start, t_end, bar_width)

        val = self.physics_data['force']
        t_string = f"{val:.2f}"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = t_end
        rc.bottom = t_end[1] - 5
        self.engine.display.blit(srf, rc)

    def draw_depth_gauge(self):
        length = 200
        start_point = (self.center_x, self.center_y - (length // 2))
        end_point = (self.center_x, self.center_y + (length // 2))

        pg.draw.line(self.engine.display, self.color, start_point, end_point, width=1)
        pg.draw.line(self.engine.display, self.color, start_point, (start_point[0] - 10, start_point[1]), 1)
        pg.draw.line(self.engine.display, self.color, end_point, (end_point[0] - 10, end_point[1]), 1)


        # Drawing the depth gauger with a triangle and current depth string:
        gauge_pos = [self.center_x, self.center_y]
        gauge_color = clr.RED
        gauge_pos[1] = start_point[1] + (length *(self.depth["current"] / self.full_depth))

        point0 = (gauge_pos[0]-5, gauge_pos[1])
        poit1_top = (point0[0] + 10, point0[1]-5)
        poit1_btm = (point0[0] + 10, point0[1]+5)
        pg.draw.line(self.engine.display, gauge_color, point0, poit1_top, 1)
        pg.draw.line(self.engine.display, gauge_color, point0, poit1_btm, 1)
        pg.draw.line(self.engine.display, gauge_color, poit1_top, poit1_btm, 1)

        font = self.font_10
        depth_str = f"{self.depth['current']:.1f}m"

        srf = font.render(depth_str, True, gauge_color)
        rc = srf.get_rect()
        rc.center = gauge_pos
        rc.right = gauge_pos[0] - 8
        self.engine.display.blit(srf, rc)

        pressure_str = f"{self.water_props['pressure']:.1f}bar"
        srf = font.render(pressure_str, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = gauge_pos
        rc.left = gauge_pos[0] + 10
        self.engine.display.blit(srf, rc)

        # range text (top depth / bottom depth)
        depth_str = f"{self.depth['top']:.1f}"
        srf = font.render(depth_str, True, self.color)
        rc = srf.get_rect()
        rc.center = start_point
        rc.right = start_point[0]
        rc.bottom = start_point[1] - 2
        self.engine.display.blit(srf, rc)

        depth_str = f"{self.depth['btm']:.1f}"
        srf = font.render(depth_str, True, self.color)
        rc = srf.get_rect()
        rc.center = end_point
        rc.right = end_point[0]
        rc.top = end_point[1] + 2
        self.engine.display.blit(srf, rc)

    def draw_engine_gauge(self):
        length = 60
        start_point = (self.center_x+60, self.center_y)
        end_point = (start_point[0]+length, self.center_y)

        pg.draw.line(self.engine.display, self.color, start_point, end_point, width=1)

        thrust_line_len = 100 * self.engine_data["thrust"]
        t_start = (start_point[0], start_point[1])
        t_end = (start_point[0], start_point[1]-thrust_line_len)
        pg.draw.line(self.engine.display, clr.RED, t_start, t_end, 10)

        font = self.font_10
        perc = int(self.engine_data['thrust'] * 100)
        t_string = f"{perc}%"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = t_end
        if self.engine_data['thrust'] >= 0:
            rc.bottom = t_end[1] - 5
        else:
            rc.top = t_end[1] + 5
        self.engine.display.blit(srf, rc)


        spray_line_len = 100 * self.engine_data["spray"]
        t_start = (start_point[0]+30, start_point[1])
        t_end = (start_point[0]+30, start_point[1] - spray_line_len)
        pg.draw.line(self.engine.display, clr.RED, t_start, t_end, 10)

        font = self.font_10
        perc = int(self.engine_data['spray'] * 100)
        t_string = f"{perc}%"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = (t_end[0], t_end[1])
        if self.engine_data['spray'] >= 0:
            rc.bottom = t_end[1] - 5
        else:
            rc.top = t_end[1] + 5
        self.engine.display.blit(srf, rc)

        buoyancy_len = 100 * (self.engine_data["buoyancy"])
        t_start = (start_point[0] + 60, start_point[1])
        t_end = (start_point[0] + 60, start_point[1] - buoyancy_len)
        pg.draw.line(self.engine.display, clr.BLUE, t_start, t_end, 10)

        font = self.font_10
        # perc = int(self.engine_data['buoyancy'] * 100)
        t_string = f"{self.engine_data['buoyancy']:.2f}"
        srf = font.render(t_string, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = (t_end[0], t_end[1])
        if self.engine_data['buoyancy'] >= 0:
            rc.bottom = t_end[1] - 5
        else:
            rc.top = t_end[1] + 5
        self.engine.display.blit(srf, rc)

    def draw_gauge_arrow(self, arrow_length: float, angle:float, center:tuple, color=clr.RED):
        # Drawing arrow from given center, with little tail on back:
        center_x, center_y = center
        tail_angle = math.radians(angle - 180)
        angle = math.radians(angle)

        arrow_x = center_x + arrow_length * math.cos(angle)
        arrow_y = center_y - arrow_length * math.sin(angle)
        pg.draw.line(self.engine.display, color, center, (arrow_x, arrow_y), 1)

        tail_len = arrow_length * 0.4
        tail_x = center_x + tail_len * math.cos(tail_angle)
        tail_y = center_y - tail_len * math.sin(tail_angle)
        pg.draw.line(self.engine.display, color, center, (tail_x, tail_y), 3)

        pg.draw.circle(self.engine.display, clr.WHITE, center, 2, 1)

    def draw_circ_gauge(self, center:tuple, sign:str, value:float, gauge_range:tuple, model:str, label:str, label_pos="btm"):
        radius = 32
        arrow_length = radius - 5
        # pos_x = 55
        # pos_y = 512
        # center = (pos_x, pos_y)
        # thrust = self.engine_data["thrust"]
        pos_x, pos_y = center

        pg.draw.circle(self.engine.display, clr.WHITE, center, radius, 1)
        font = self.font_10
        srf = font.render(f"{value:.1f}", True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = (pos_x, pos_y + radius - 16)
        self.engine.display.blit(srf, rc)

        ranged_val = 0
        gauge_min, gauge_max = gauge_range
        # evaluated_label = "..."
        if model == 'pressure':
            # evaluated_label = f"{label} = {value:.1f} bar"
            ranged_val = Tools.range_value(value, gauge_min, gauge_max, 0, 1)
        elif model == 'temp':
            # evaluated_label = f"{label} = {value:.1f} °C"
            ranged_val = Tools.range_value(value, gauge_min, gauge_max, 0, 1)
        elif model == "DPF":
            # evaluated_label = f"{label} = {value:.2f} /sec"
            ranged_val = Tools.range_value(value, 0, 10, 0, 1)

        if ranged_val > 0:
            angle = 230 - 280*ranged_val
        else:
            angle = 230

        srf = font.render(label, True, clr.WHITE)
        rc = srf.get_rect()
        if label_pos == "btm":
            rc.center = (pos_x, pos_y + radius + 10)
        else:
            rc.center = (pos_x, pos_y - radius - 10)
        self.engine.display.blit(srf, rc)

        # draw signs:
        low_start_angle = 228
        low_end_angle = 150
        mid_end_angle = 10
        hight_end_angle = -50

        sradius = radius-10
        arc_rect = (pos_x - sradius, pos_y - sradius, sradius*2, sradius*2)
        pg.draw.arc(self.engine.display, clr.GREEN, arc_rect, math.radians(low_end_angle), math.radians(low_start_angle), 5)
        pg.draw.arc(self.engine.display, clr.YELLOW, arc_rect, math.radians(mid_end_angle), math.radians(low_end_angle), 5)
        pg.draw.arc(self.engine.display, clr.RED, arc_rect, math.radians(hight_end_angle), math.radians(mid_end_angle), 5)

        self.draw_gauge_arrow(arrow_length, angle, center)


    def draw_risk_gauge(self):
        bg_image = pg.image.load("img/interface/risk-gauge.png").convert()
        bg_image.set_colorkey(clr.BLACK)
        bg_rect = bg_image.get_rect()
        x_pos = 250
        y_pos = 63
        bg_rect.topleft = (x_pos, y_pos)
        self.engine.display.blit(bg_image, bg_rect)

        font = self.font_10
        srf = font.render("RISK", True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = bg_rect.center
        rc.bottom = bg_rect.top - 4
        self.engine.display.blit(srf, rc)

        line_len_min = 0
        line_len_max = bg_rect.height - 5

        # --> Get the risk value and transform it to line_len:
        risk = self.engine.sub.physics.surrounding_risk
        line_len = Tools.range_value(risk, 0, 1, line_len_min, line_len_max)

        if line_len > line_len_max:
            line_len = line_len_max

        start_point = (bg_rect.center[0], int(bg_rect.center[1] - 2 + bg_rect.height//2))
        end_point = (bg_rect.center[0], start_point[1]-line_len)

        if line_len > 0:
            pg.draw.line(self.engine.display, clr.RED, start_point, end_point, width=10)


        arrow_len = 18
        arr_start_point = (bg_rect.center[0]-6, end_point[1])
        arr_end_point = (arr_start_point[0]+arrow_len, end_point[1])

        pg.draw.line(self.engine.display, clr.WHITE, arr_start_point, arr_end_point, width=1)

        srf = font.render(f"{int(risk*100)} %", True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = arr_end_point
        rc.left = arr_end_point[0] + 5
        self.engine.display.blit(srf, rc)


    def draw_circ_gauges(self):
        temperature = 80.2
        y_pos = 95
        x_pos = 55
        gauge_distance = 75

        # TODO: get pressure from depth.
        # pressure = self.pressure_from_depth(self.depth['current'])
        pressure = self.water_props["pressure"]
        gauge_range = (0, 110)
        self.draw_circ_gauge((x_pos, y_pos), "", pressure, gauge_range, model="pressure", label="P-OUT, bar", label_pos="top")

        t_out = self.water_props["temp"]
        gauge_range = (0, 250)
        self.draw_circ_gauge((x_pos+gauge_distance, y_pos), "", t_out, gauge_range, model="temp", label="T-OUT, °C", label_pos="top")

        t_in = self.engine.sub.health.internal_temp
        gauge_range = (0, 110)
        self.draw_circ_gauge((x_pos + 2 * gauge_distance, y_pos), "", t_in, gauge_range, model="temp", label="T-IN, °C", label_pos="top")

        y_pos = 190

        # TODO: calculate damage/frame from risc * thrust_rofce

        # damage = 0.2
        # self.draw_circ_gauge((x_pos+2*gauge_distance, y_pos), "DPF", damage)


    def draw_power_gauge(self):
        """ Draw a double arrow circular gauge for power-in and power-out...
        """
        bg_image = pg.image.load("img/interface/power-gauge.png").convert()
        bg_image.set_colorkey(clr.WHITE)

        bg_rect = bg_image.get_rect()
        x_pos = 60
        y_pos = 195
        center = (x_pos, y_pos)

        radius = 40
        arrow_length = (radius-10, radius-5)  # (power-in, power-out)

        bg_rect.center = (x_pos, y_pos)
        self.engine.display.blit(bg_image, bg_rect)

        label = "PWR"

        pg.draw.circle(self.engine.display, clr.WHITE, center, radius, 1)
        font = self.font_10
        srf = font.render(label, True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = (x_pos, y_pos + radius - 15)
        self.engine.display.blit(srf, rc)

        # ranged_val = 0
        # gauge_min = (0, 0)  # (power-in, power-out)
        # gauge_max = (1, 1)
        # ranged_val = Tools.range_value(value, gauge_min, gauge_max, 0, 1)

        power_in = self.engine.sub.health.energy_gain
        power_out = self.engine.sub.health.energy_consumption["total"]  # 0: total, 1:

        if power_in > 0:
            angle_in = 230 - 280*power_in
        else:
            angle_in = 230

        if power_out > 0:
            angle_out = 230 - 280*power_out
        else:
            angle_out = 230

        # draw arrow for power-in:
        self.draw_gauge_arrow(arrow_length[0], angle_in, center, color=clr.YELLOW)
        # draw arrow for power-out:
        self.draw_gauge_arrow(arrow_length[0], angle_out, center, color=clr.RED)

    @staticmethod
    def load_battery_sheet(sheet_src="img/interface/battery-gauge.png"):
        """ The battery animation is loaded at the begining of the class. """
        sheet = pg.image.load(sheet_src).convert()
        num_frames = 11
        width = 32
        height = 64
        frame_list = []
        for f in range(num_frames):
            img = pg.Surface((width, height))
            img.blit(sheet, (0, 0), ((f * width), 0, width, height))
            img.convert()
            img.set_colorkey(clr.BLACK)
            frame_list.append(img)

        return frame_list

    def draw_warning_sign(self, pos_x, pos_y, sign_id=0, speed_up=False):
        if speed_up:
            blink_interval = 400
        else:
            blink_interval = 1100

        time_now = pg.time.get_ticks()

        img_rect = self.warning_img.get_rect()
        img_rect.center = (pos_x, pos_y)

        if time_now - self.last_warning_blink[sign_id] > blink_interval // 2:
            self.engine.display.blit(self.warning_img, img_rect)

        if time_now - self.last_warning_blink[sign_id] > blink_interval:
            self.last_warning_blink[sign_id] = time_now


    def draw_battery_gauge(self):

        # Note: center position of the gauge:
        pos_x = 130
        pos_y = 192

        charge = self.engine.sub.health.total_energy
        charge_perc = charge * 100
        current_index = math.ceil(charge * 10)
        if charge < 0.02:  # when drops  below 2% draw empty battery.
            current_index = 0

        if charge < 0.12:
            self.draw_warning_sign(pos_x, pos_y, sign_id=0, speed_up=True)
        elif charge < 0.25:
            self.draw_warning_sign(pos_x, pos_y, sign_id=0)


        img = self.battery_sheet[current_index]
        gauge_rect = img.get_rect()
        gauge_rect.center = (pos_x, pos_y)

        self.engine.display.blit(img, gauge_rect)

        font = self.font_10
        srf = font.render(f"{charge_perc:.2f}%", True, clr.WHITE)
        rc = srf.get_rect()
        rc.center = gauge_rect.center
        rc.left +=1
        rc.top = gauge_rect.bottom + 5
        self.engine.display.blit(srf, rc)

        # consumption info:
        solar = self.engine.sub.physics.solar_energy
        solar_perc = solar * 100
        thermal = self.engine.sub.physics.thermal_energy
        thermal_perc = thermal * 100

        consumption = self.engine.sub.health.energy_consumption
        thrust = consumption["thrust"] * 100
        spray = consumption["spray"] * 100

        text_left = gauge_rect.right + 5
        text_top = gauge_rect.top

        srf = font.render(f"{solar_perc:.1f} %", True, clr.YELLOW)
        rc = srf.get_rect()
        rc.left = text_left
        rc.top = text_top
        self.engine.display.blit(srf, rc)
        srf = font.render(f"{thermal_perc:.1f} %", True, clr.YELLOW)
        rc = srf.get_rect()
        rc.left = text_left
        rc.top = text_top + 13
        self.engine.display.blit(srf, rc)

        srf = font.render(f"{thrust:.1f} %", True, clr.RED)
        rc = srf.get_rect()
        rc.left = text_left
        rc.top = text_top + 26
        self.engine.display.blit(srf, rc)
        srf = font.render(f"{spray:.1f} %", True, clr.RED)
        rc = srf.get_rect()
        rc.left = text_left
        rc.top = text_top + 39
        self.engine.display.blit(srf, rc)

        total_in = solar+thermal
        if total_in > 1:
            total_in = 1
        total = (total_in - consumption["total"]) * 100

        pg.draw.line(self.engine.display, clr.WHITE, (text_left-3, text_top + 51), (text_left-3 + 40, text_top+51))
        if total >= 0:
            srf = font.render(f"{total:.1f} %", True, clr.YELLOW)
        else:
            srf = font.render(f"{total:.1f} %", True, clr.RED)
        rc = srf.get_rect()
        rc.left = text_left
        rc.top = text_top + 55
        self.engine.display.blit(srf, rc)


    def draw_heading_gauge(self):
        # self.heading_gauge_images = {
        #     "gauge": gauge_img,
        #     "sub": sub_img
        # }
        # Note: center coordinates
        pos_x = 270
        pos_y = 190

        gauge_img = self.heading_gauge_images["gauge"]
        gauge_rect = gauge_img.get_rect()
        gauge_rect.center = (pos_x, pos_y)
        self.engine.display.blit(gauge_img, gauge_rect)

        sub_img = self.heading_gauge_images["sub"].copy()
        sub_rect = sub_img.get_rect()
        sub_rect.center = (pos_x, pos_y)
        heading = self.engine.sub.heading
        # --- rotation:
        if not heading == 0:
            sub_img = pg.transform.rotate(sub_img, heading)
            sub_rect = sub_img.get_rect()
            sub_rect.center = (pos_x, pos_y)

        self.engine.display.blit(sub_img, sub_rect)

        font = self.font_10
        srf = font.render(f"{heading:.1f} deg", True, clr.WHITE)
        rc = srf.get_rect()
        rc.left = gauge_rect.right - 10
        rc.top = gauge_rect.top + 10
        self.engine.display.blit(srf, rc)

        struc_buoyancy = self.engine.sub.health.structural_buoyancy
        label = f"SBY: {struc_buoyancy:.2f}"

        srf = font.render(label, True, clr.BLUE)
        rc = srf.get_rect()
        rc.right = gauge_rect.left + 20
        rc.top = gauge_rect.bottom - 15
        self.engine.display.blit(srf, rc)

        integrity_perc = self.engine.sub.health.integrity * 100
        label = f"INTGR: {integrity_perc:.1f} %"

        srf = font.render(label, True, clr.WHITE)
        rc = srf.get_rect()
        rc.right = gauge_rect.left + 35
        rc.top = gauge_rect.top
        self.engine.display.blit(srf, rc)

        damage_rate = self.engine.sub.health.damage_rate
        if damage_rate > 0:
            self.draw_warning_sign(pos_x, pos_y, sign_id=1, speed_up=True)

        coord_x = self.engine.sub.pos_x
        coord_y = self.engine.sub.pos_y
        cell_id_x = int(coord_x // MapSettings.CELL_SIZE)
        cell_id_y = int(coord_y // MapSettings.CELL_SIZE)
        # distance = self.engine.sub.physics.distance_from_pixels(coord_x)
        # depth = self.engine.sub.physics.depth_from_pixels()
        label = f"COORD: {cell_id_y}-{cell_id_x}"

        srf = font.render(label, True, clr.RED)
        rc = srf.get_rect()
        rc.left = gauge_rect.right - 35
        rc.top = gauge_rect.bottom - 10
        self.engine.display.blit(srf, rc)

    def draw(self):
        self.draw_depth_gauge()
        self.draw_engine_gauge()
        self.draw_resistance_gauge()

        self.draw_circ_gauges()

        self.draw_risk_gauge()

        self.draw_power_gauge()
        self.draw_battery_gauge()

        self.draw_heading_gauge()


class Terminal:
    POS_X = 35
    POS_Y = 490

    def __init__(self, engine):
        self.engine = engine

        self.bgr_image = pg.image.load("img/interface/terminal-bgr.png").convert()
        self.bgr_image.set_colorkey(clr.WHITE)
        self.bgr_rect = self.bgr_image.get_rect()
        self.bgr_rect.topleft = (self.POS_X, self.POS_Y)

        self.font_size = 12
        self.font_10 = pg.font.Font("freesansbold.ttf", self.font_size)

        self.lines = []
        self.max_lines_num = 10

    def print(self, text):
        # add a line to terminal
        self.lines.append(text)
        if len(self.lines) > self.max_lines_num:
            self.lines.pop(0)

    def clear(self):
        self.lines = []

    def update(self):
        ...

    def wrap_line(self, text_line, max_width):

        lines = []

        words = text_line.split()
        current_line = ""

        for word in words:
            if len(current_line) + len(word) <= max_width:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        return lines

    def draw_lines(self):
        max_width = 40

        font = self.font_10

        line_y = 0
        # Note: used to distinguish real lines and lines, generated by word-wrap

        for line in self.lines:
            line = f"> {line}"

            if len(line) > max_width:
                wrap_lines = self.wrap_line(line, max_width)

                for i, ln in enumerate(wrap_lines):
                    if i > 0:
                        ln = f"    {ln}"
                    srf = font.render(ln, True, clr.YELLOW)
                    rc = srf.get_rect()
                    rc.left = self.POS_X + 5
                    rc.top = 5 + self.POS_Y + self.font_size * line_y
                    self.engine.display.blit(srf, rc)
                    line_y += 1

            else:
                srf = font.render(line, True, clr.YELLOW)
                rc = srf.get_rect()
                rc.left = self.POS_X + 5
                rc.top = 5 + self.POS_Y + self.font_size * line_y

                self.engine.display.blit(srf, rc)
                line_y += 1

    def draw(self):
        self.engine.display.blit(self.bgr_image, self.bgr_rect)
        # TODO: draw the text...
        self.draw_lines()

class InfoService:

    # TODO: ======= Info Service should be REVISED, reducing the complexity!

    def __init__(self, engine):
        self.engine = engine
        self.screen_center = (self.engine.width // 2, self.engine.height // 2)

        self.default_font = pg.font.Font("freesansbold.ttf", 12)

        self.surface = None

        self.items = [
            {
                "id": 0,
                "text": "",
                "font": pg.font.Font("freesansbold.ttf", 10),
                "color": clr.WHITE,
                "surface": None,
                "rect": None,
                "smooth-font": True,
                "pos": (self.screen_center[0], 20)
            },
            {
                "id": 1,
                "text": "",
                "font": pg.font.Font("freesansbold.ttf", 10),
                "color": clr.WHITE,
                "surface": None,
                "rect": None,
                "smooth-font": True,
                "pos": (self.screen_center[0], 35)
            },

            {
                "id": 2,
                "text": "",
                "font": pg.font.Font("freesansbold.ttf", 10),
                "color": clr.WHITE,
                "surface": None,
                "rect": None,
                "smooth-font": True,
                "pos": (self.screen_center[0], 50)
            },
            {
                "id": 3,
                "text": "",
                "font": pg.font.Font("freesansbold.ttf", 10),
                "color": clr.WHITE,
                "surface": None,
                "rect": None,
                "smooth-font": True,
                "pos": (self.screen_center[0], 65)
            }

        ]

        self.last_draw = pg.time.get_ticks()
        self.draw_interval = 20

    @staticmethod
    def item_validation(item: dict):
        valid_values = ["id", "text", "font-size", "color", "smooth-font", "pos"]
        for val in valid_values:
            if val not in item.keys():
                return False
        return True

    def add_item(self, interface_item: dict):
        if self.item_validation(interface_item):
            self.items.append(interface_item)

    def update_item(self, item_id:int, new_text:str):
        if item_id < len(self.items):
            self.items[item_id]["text"] = new_text
            self.items[item_id]["surface"] = self.items[item_id]["font"].render(new_text, self.items[item_id]["smooth-font"], self.items[item_id]["color"])

    def draw(self):

        for item in self.items:
            if item["surface"] is not None:
                item_rect = item["surface"].get_rect()
                item_rect.center = item["pos"]

                self.engine.display.blit(item["surface"], item_rect)

            # item_font = font.Font("freesansbold.ttf", item["font-size"])
            # item_surface = item_font.render(item["text"], item["smooth-font"], item["color"])
            # item_rect = item_surface.get_rect()
            # item_rect.center = item["pos"]
            #
            # self.engine.display.blit(item_surface, item_rect)

    def draw_system_only(self):
        item = self.items[0]

        if item["surface"] is not None:
            item_rect = item["surface"].get_rect()
            item_rect.center = item["pos"]

            self.engine.display.blit(item["surface"], item_rect)


class MainMenu:
    """ TODO: It may be used for show/hide editors, load and save the maps"""
    def __init__(self, engine):
        self.engine = engine

        self.screen_center = (self.engine.width // 2, self.engine.height //2)

        ...

        self.items = [
            {"id": 0,
             "text": "MAP EDITOR",
             "pos": (0, 0)},
        ]




    def draw(self):
        ...

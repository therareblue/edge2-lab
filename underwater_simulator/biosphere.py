import random
from math import ceil

from typing import List
import json

import pygame as pg
from settings import MapSettings, FileLocations as files, ColorPalette as clr
from tools import Tools as tools

from dbase import BioImageUnit

"""
    Everything that is independent from map cells and is free to move,
    is managed here, including water, fish, shellfish, etc.
    Note: Submarine is not included here, but in separate module.
"""

class Air:
    def __init__(self, engine):
        self.engine = engine
        self.shallow_water = engine.seawater_shallow

        self.num_images = self.shallow_water.num_images
        self.raw_image = pg.image.load(f"{files.WATER_IMAGES}shallow_top.png")
        self.raw_image_large = pg.image.load(f"{files.WATER_IMAGES}air.png")




        # 1. Create a mask with the size of num_images * raw_image width.
        self.image_width = self.raw_image.get_width() * self.num_images
        self.image_height = self.raw_image.get_height()
        self.large_height = self.raw_image_large.get_height()

        self.image = pg.surface.Surface((self.image_width, self.image_height))
        self.image_large = pg.surface.Surface((self.image_width, self.large_height))
        # self.image.fill(clr.WHITE)

        for i in range(self.num_images):
            x_coord = i * self.raw_image.get_width()
            self.image.blit(self.raw_image, (x_coord, 0))
            self.image_large.blit(self.raw_image_large, (x_coord, 0))

        self.image.convert()
        self.image.set_colorkey(clr.WHITE)

        self.image_large.convert()
        self.image_large.set_colorkey(clr.WHITE)
        self.large_mask = pg.mask.from_surface(self.image_large)

        # self.image.convert()
        # self.image.set_colorkey(clr.SHALLOW)
        self.mask = pg.mask.from_surface(self.image)


        # self.debug_img = self.mask.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=clr.BLUE)

        self.top = self.shallow_water.pos_y - 24
        # Note: there are 24px difference between the surface_water_img and shallow_top img, which are compensated.

        # Where the submarine should start checking for mask collision with the water surface:
        # self.floating_check_start_from = self.top + self.image.get_height() + 20
        self.floating_check_start_from = self.top + 270

        self.scroll_x = 0


    def update(self):
        # if abs(self.scroll_x) >= self.rect.width:
        #     self.scroll_x = 0
        # else:
        #     self.scroll_x -= self.scroll_speed
        self.scroll_x = self.shallow_water.scroll_x

    # def debug_draw(self):
    #     x_coord = (self.shallow_water.scroll_x - self.engine.scroll_x)
    #     self.engine.display.blit(self.debug_img, (x_coord, self.top - self.engine.scroll_y))


class Water:
    """ For every water part will be created an instance of Water class in teh main module.
        Water has color, image and scrolling speed, which if set, it causes water to flow.
    """
    def __init__(self, engine, props:dict, img_file:str=None, scrolling_speed:int=0):
        self.engine = engine

        self.props = props
        # {"color":(0, 0, 0), "resistance": 3, "temp":8}

        self.last_random_update = pg.time.get_ticks()
        self.update_interval = 1000

        # IMAGE:
        if img_file is not None:
            self.image = pg.image.load(img_file).convert()
            self.image.set_colorkey(clr.WHITE)
            self.rect = self.image.get_rect()
            self.mask = pg.mask.from_surface(self.image)

        else:
            self.image = None
            self.rect = None
            self.mask = None
            self.surface_mask = None

        self.scroll_speed = scrolling_speed
        self.scroll_x = 0

        self.pos_x = 0
        self.pos_y = self.props["deep"]

        # Maximum depth of the water. Note: Total depth will be pos_y + self.depth
        self.depth = self.props["depth"]

        if self.depth is not None:
            self.total_depth = self.pos_y + self.depth
        else:
            self.depth = self.engine.height

        if self.rect is not None:
            self.rect.topleft = [self.pos_x, self.pos_y]

        # how many times the image is printed side by side to fill the screen:
        self.num_images = 2

        # A rect is used to fill the area below the water mask. Mask is thinner than the area covered by the water.
        # - This Rect parameters are used to check if submerged unit is in that water...
        self.below_fill = None

    # def get_water_temperature(self, pos_y):
    #     if pos_y > self.props["deep"]:
    #         # if depth is None, this means we check till infinity.
    #         if self.props["depth"] is not None:
    #             if pos_y < self.props["depth"]:
    #                 return self.props["temp"]
    #         else:
    #             return self.props["temp"]
    #
    #     return None

    # def get_temp_and_depth(self):
    #     return self.props["temp"], self.pos_y

    def random_update_props(self):
        now_is = pg.time.get_ticks()
        if now_is - self.last_random_update > self.update_interval:
            temp = self.props["temp"]
            min_t = self.props["min-temp"]
            max_t = self.props["max-temp"]
            change_rate = 1

            # delta = random.choice([1, 0, -1])
            # if delta > 0 and temp < max_temp:
            #     temp += delta
            # elif delta < 0 and temp > min_temp:
            #     temp += delta
            new_temp = tools.random_value_change(temp, min_t, max_t, change_rate)

            self.props["temp"] = new_temp

            self.last_random_update = now_is

    def update(self):
        # Animation:

        if self.image is not None:
            if abs(self.scroll_x) >= self.rect.width:
                self.scroll_x = 0
            else:
                self.scroll_x -= self.scroll_speed

        # Props Change:
        self.random_update_props()

    def draw(self):
        # filling the rest of the screen with the color of the water
        # Note: The image height is way smaller than the  map. This is why we fill the rest with the same color.
        if self.props["id"] == 0:
            pg.draw.rect(self.engine.display, clr.SHALLOW, (0-self.engine.scroll_x, self.props["deep"]+self.rect.height-self.engine.scroll_y, self.engine.width+self.engine.scroll_x, self.engine.height+self.engine.scroll_y))
        elif self.props["id"] == 1:
            pg.draw.rect(self.engine.display, clr.DEEP, (0-self.engine.scroll_x, self.props["deep"]+self.rect.height-self.engine.scroll_y, self.engine.width+self.engine.scroll_x, self.engine.height+self.engine.scroll_y))
        
        # placing the water images.
        for i in range(self.num_images):
            x_coord = (self.scroll_x - self.engine.scroll_x) + i * self.rect.width
            self.engine.display.blit(self.image, (x_coord, self.rect.y - self.engine.scroll_y))


class LifeUnit:
    # LifeForm
    def __init__(self, id, image_unit: BioImageUnit, left, top):

        self.id = id
        self.base_image = image_unit.image  # refference to the image_library main_image.
        self.animation = image_unit.animation  # refference to the image_library animation
        self.mask = image_unit.mask

        self.description = image_unit.description

        self.width = self.base_image.get_width()
        self.height = self.base_image.get_height()

        # Used when saving the biolife to file
        self.address = {
            "ref-id": image_unit.id,
            "library": image_unit.library,
            "left": left,
            "top": top,
        }

        self.left = left
        self.top = top

        self.props = image_unit.default_props.copy()
        # Note: props may individually changed over time, so it is copied from default, instead of referencing.

        self.rect = self.base_image.get_rect()

        self.frame_id = 0

        # The animation is in self.animation.speed
        self.last_frame_change = pg.time.get_ticks()

        print(f"Created new Life Unit: location=({self.top}, {self.left}), size=({self.width, self.height})")

    @property
    def map_coverage(self):
        """ Returns tuple with format (start_cell, start_row, end_cell, end_row)"""
        start_col_index = int(self.left // MapSettings.CELL_SIZE)
        start_row_index = int(self.top // MapSettings.CELL_SIZE)
        end_col_index = int(start_col_index + (self.width // MapSettings.CELL_SIZE))
        end_row_index = int(start_row_index + (self.height // MapSettings.CELL_SIZE))
        return start_col_index, start_row_index, end_col_index, end_row_index


    def update(self, now):
        if self.animation is not None:
            if now - self.last_frame_change > self.animation.speed:
                self.frame_id += 1
                if self.frame_id >= self.animation.frames_count:
                    self.frame_id = 0

                self.last_frame_change = now

    def draw(self, display, scroll_x, scroll_y):
        self.rect.left = self.left - scroll_x
        self.rect.top = self.top - scroll_y

        if self.animation is not None:
            display.blit(self.animation.get_frame(self.frame_id), self.rect)
        else:
            # the biolife is static. only draw the image:
            display.blit(self.base_image, self.rect)


class BioLife:
    def __init__(self, engine):
        self.engine = engine

        self.life_list:List[LifeUnit] = []  # <-- a list of life units. See the class above.
        self.animation_speed = 100

    # -> Used to check for collision, and extract unit properties
    def get_unit_info(self, unit_id):
        """ Return reference to LifeUnit from id.
        """
        if 0 <= unit_id < len(self.life_list):
            unit_info = {
                "description": self.life_list[unit_id].description,
                "props": self.life_list[unit_id].props
            }
            return unit_info
        else:
            return None

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                loaded_file_data = json.load(file)
                # Note: loaded_file_data is a list of dictionaries

                if self.life_list:
                    self.life_list.clear()

                for i, data_line in enumerate(loaded_file_data):
                    ref_id = data_line['ref-id']
                    library = data_line['library']
                    left = data_line['left']
                    top = data_line['top']

                    image_unit = self.engine.image_library.biolife_images[library][ref_id]
                    life_unit = LifeUnit(i, image_unit, left, top)
                    self.life_list.append(life_unit)

            return f"BioLife loaded successfully, with {len(loaded_file_data)} life-forms."

        except FileNotFoundError:
            return "Biolife File does not exists. No biolife loaded."
        except Exception as e:
            return f"Loading BioLife data file FAILED: {e}"

    def save_to_file(self, filename):
        if self.life_list:
            try:
                with open(filename, 'w') as file:
                    saving_json_data = [unit.address for unit in self.life_list]
                    json.dump(saving_json_data, file)

                    return f"BioLife data saved successfully in '{filename}' file."

            except Exception as e:
                return f"Saving BioLife file FAILED: {e}"

        else:
            return "Life list is empty. No biolifes found on map, and save is aborted."

    def map_correct(self):
        # saving the corrected map structure. Used only to repair the map:
        # for row in range(self.engine.map.cells_y):
        #     for col in range(self.engine.map.cells_x):
        #         self.engine.map.map_structure[row][col].append([])
        for row in range(self.engine.map.cells_y):
            for col in range(self.engine.map.cells_x):
                self.engine.map.map_structure[row][col][3] = []

        # for i, life_unit in enumerate(self.life_list):
        #     map_coverage = life_unit.map_coverage
        #     for row in range(map_coverage[1], map_coverage[3] + 1):
        #         for col in range(map_coverage[0], map_coverage[2] + 1):
        #             if i not in self.engine.map.map_structure[row][col][3]:
        #                 self.engine.map.map_structure[row][col][3].append(i)

        print(f"Map corrected:")
        print(f"first={self.engine.map.map_structure[0][0]} | last={self.engine.map.map_structure[-1][-1]}")

    def add_life_unit(self, ref_id, library_name, mouse):
        # 1. Get the placement coordinates:
        pos_x, pos_y = mouse

        # 2. re-position the placement coordinates to stick into the map cells top-left:
        map_cell_size = self.engine.map.cell_size
        topleft_cell_index = (pos_x + self.engine.scroll_x) // map_cell_size
        topleft_row_index = (pos_y + self.engine.scroll_y) // map_cell_size

        top_position = int(topleft_row_index * map_cell_size)
        left_position = int(topleft_cell_index * map_cell_size)

        # 3. Get reference to the BioImageUnit on the engine.image_library:
        image_unit = self.engine.image_library.biolife_images[library_name][ref_id]

        # 4. Delete a unit if there is one in the same position:
        self.delete_life_unit(mouse)

        life_unit_id = len(self.life_list)

        # 5. Create a new life unit and append it to the life list:
        life_unit = LifeUnit(life_unit_id, image_unit, left_position, top_position)
        if life_unit is not None:
            self.life_list.append(life_unit)
            result = ["Added new life unit on the map",f"Total life_list size = {len(self.life_list)}"]
        else:
            return [f"Adding life unit with ref-id={ref_id} FAILED."]

        # 6. On every covered map-cell from map.map_structure (syntax: [(None, 0, 0, []), ...]
        #    append to the 4th element (list) the index of the newly created life unit.
        #    Used for the vision, to faster determine if in some cell, there is life unit located.



        # -write the life_unit_id on every map cell covered by the unit:
        map_coverage = self.life_list[-1].map_coverage

        for row in range(map_coverage[1], map_coverage[3]):
            for col in range(map_coverage[0], map_coverage[2]):
                if life_unit_id not in self.engine.map.map_structure[row][col][3]:
                    self.engine.map.map_structure[row][col][3].append(life_unit_id)

        # # -get number of cells and rows covered:
        # covered_cells = life_unit.width // map_cell_size
        # covered_rows = life_unit.height // map_cell_size
        #
        # # - for all covered map-cell indexes add the id of the new life unit:
        # for row in range(topleft_row_index, covered_rows+1):
        #     for col in range(topleft_cell_index, covered_cells+1):
        #         self.engine.map.map_structure[row][col][3].append(life_unit_id)

        return result

        # TODO: Add check for row and cell indexes if they went out the map size

    def get_unit_id(self, mouse):
        """ Get the first found unit address (unit id in the life_list) of the unit,
            located on the mouse coordinates...
        """
        mouse_x = mouse[0] + self.engine.scroll_x
        mouse_y = mouse[1] + self.engine.scroll_y
        # Returns a unit id based of the coordinates of the map, FIRST FOUND
        for i, unit in enumerate(self.life_list):
            if unit.left < mouse_x < unit.left+unit.width:
                if unit.top < mouse_y < unit.top+unit.height:
                    return i
        return None

    def delete_life_unit(self, mouse):
        # Deleting a unit based on its location on the map
        # Note: the coordinates come from the mouse pointer
        element_id = self.get_unit_id(mouse)
        if element_id is not None and element_id < len(self.life_list):

            map_coverage = self.life_list[element_id].map_coverage
            for row in range(map_coverage[1], map_coverage[3]+1):
                for col in range(map_coverage[0], map_coverage[2]+1):
                    if element_id in self.engine.map.map_structure[row][col][3]:
                        self.engine.map.map_structure[row][col][3].remove(element_id)

            del self.life_list[element_id]
            result = [f"A life unit, listed under index={element_id} deleted.", f"total _life_list size = {len(self.life_list)}"]
            return result
        return None

    def unit_id_list_from_coordinates(self, map_coordinates):
        """ id list of all life units located on given coordinates.
            Note: Even we place only one unit on same coordinates, some units are moving in time and may cross others.
        """
        id_list = []
        coord_x, coord_y = map_coordinates
        for i, unit in enumerate(self.life_list):
            if unit.left < coord_x < unit.left+unit.width:
                if unit.top < coord_y < unit.top+unit.height:
                    id_list.append(i)

        return id_list

    def update(self):
        # animates all biolife images, changing its frame-id
        now = pg.time.get_ticks()
        for unit in self.life_list:
            unit.update(now)

    def draw(self):
        # Drawing only the life units, with top and left inside the current screen...
        for unit in self.life_list:
            # if (self.engine.scroll_x-unit["width"]) <= unit["left"] < self.engine.scroll_x+self.engine.width:
            #     # TODO: same for top...
            #     # NOTE: use the lifeUnit draw method for visualization. Here only select the visible units.
            #     ...
            unit.draw(self.engine.display, self.engine.scroll_x, self.engine.scroll_y)
        ...
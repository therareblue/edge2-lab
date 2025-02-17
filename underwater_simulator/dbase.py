"""
All databases are stored and managed here.
"""
import os
import json
import pygame as pg

from settings import MapSettings, FileLocations as files, ColorPalette as clr
from typing import List


class Animation:
    def __init__(self, sheet_src:str, frame_width:int, frame_height: int, frames_count:int, animation_speed:int=0, background_color:tuple=(255, 255, 255)):
        self._sprite_sheet = pg.image.load(sheet_src).convert()
        self._sprite_sheet.set_colorkey(background_color)

        self.background_color = background_color
        self.width = frame_width
        self.height = frame_height

        self.frames_count = frames_count
        self.speed = animation_speed  # if left 0, the animation will be with the speed of screen update.

        self._frames = []
        self._split()


    def _get_frame_image(self, frame):
        frame_image = pg.Surface((self.width, self.height))
        frame_image.fill(self.background_color)
        frame_area = ((frame * self.width), 0, self.width, self.height)
        frame_image.blit(self._sprite_sheet, (0, 0), frame_area)
        frame_image.convert()
        frame_image.set_colorkey(self.background_color)
        return frame_image

    def _split(self):
        for f in range(self.frames_count):
            img = self._get_frame_image(frame=f)
            self._frames.append(img)

    def get_frame(self, frame_id):
        return self._frames[frame_id]


class Cell:
    """ Keeps all properties of a cell,
        loaded from the image library json file...
    """
    def __init__(self, cell_size:int, base_unit_image:pg.image, cell_image:pg.image, unit_description:str, cell_props:dict, mask_color=None, clear_cell=False):

        self.description = unit_description
        # the cell size. Every cell is a rectangle with (cell_size, cell_size) size.
        self.size = (cell_size, cell_size)

        # keeps the main image, for elements covering several cells.
        self.base_image = base_unit_image

        # If the element covers several cells, their images are here.
        self.image = cell_image

        # used for collision detection
        if clear_cell:
            self.mask = None
        else:
            if mask_color is not None:
                mask_img = cell_image.copy()
                mask_img.set_colorkey(mask_color)
                self.mask = pg.mask.from_surface(mask_img)
            else:
                self.mask = pg.mask.from_surface(cell_image)
        # TODO: Check if the mask needs to set the setcolor and unsetcolor colors

        # Used to affect the submarine and other moving objects
        self.props = cell_props




class CellularImageUnit:
    """ The map unit represent an element created from map images.
        Every map unit has a list of cells with shape [x, y] or [cols, rows]
        used to place the object in the map cellular matrix.
    """
    CELL_SIZE: int = MapSettings.CELL_SIZE


    def __init__(self, element_id:int, palette, filename: str, unit_data: dict):

        self.id = None
        self.palette = None
        self.description = None

        # The base image used for the MapEditor tool visualization
        self.image = None

        # Structure is list of elements, in order from the json file.
        self.structure = []
        # mapping the places of the images for placing on map (rows, cols)
        self.structure_map = []

        self.unit_data = None

        self.success = self.create(element_id, palette, filename, unit_data)

    def create(self, element_id:int, palette, filename: str, unit_data: dict):
        # -->1. Get the size of the Unit:
        # print(unit_data)
        cols, rows = unit_data["shape"]

        # -->2. Validation
        if not self.CELL_SIZE == 32:
            # TODO: Add functionality to autoresize all units based on the cell_size.
            print("There is no functionality to resize units yet!")
            return False
        if not os.path.isfile(filename):
            print(f"Filename '{filename}' does NOT EXISTS or is NOT A FILE.")
            return False
        if not filename.endswith('.png'):
            print(f"Filename '{filename}' does is not valid .png file.")
            return False
        if not unit_data:
            print(f"Invalid file properties: {unit_data}")
            return False

        self.id = element_id
        self.palette = palette
        self.description = unit_data["description"]

        # used for info services only
        self.unit_data = unit_data

        # -->3. Load the image from file.
        self.image = pg.image.load(filename).convert()
        self.image.set_colorkey(clr.WHITE)

        # Since unit_data["props"] is 1D array, we need to track the right index,
        # based on the number of iterations in our 2D loop:
        cell_index = 0

        # -->4. Split the image into cells and create the cell objects:
        for row in range(rows):

            # collects all cell id. Then cells_row appends to the cls.structure_map list
            structure_map_row = []

            for col in range(cols):
                # -create the cell image
                cell_image = pg.Surface((self.CELL_SIZE, self.CELL_SIZE))
                start_x = col * self.CELL_SIZE
                start_y = row * self.CELL_SIZE
                end_x = start_x + self.CELL_SIZE
                end_y = start_y + self.CELL_SIZE
                cell_image.fill(clr.WHITE)
                cell_image.blit(self.image, (0, 0), (start_x, start_y, end_x, end_y))
                cell_image.convert()
                cell_image.set_colorkey(clr.WHITE)
                # Note: We can use the BLACK bgr of the Surface with colorkey=BLACK, instead of making it WHITE,
                # but since we use WHITE bgr across all images, the image may have black parts in it.

                mask_color = unit_data["mask-clr"] if "mask-clr" in unit_data.keys() else None
                # Note: if the bgr color is red (for hot_water) instead of white, 'set_colorkey()' will take no effect.
                #   but the mask_color will later clear the cell-mask bgr...

                # -get the props
                props = unit_data["props"][cell_index]

                # -create the cell element and append it to the cls.structure list:
                if palette is not None:
                    single_cell = Cell(self.CELL_SIZE, self.image, cell_image, self.description, props, mask_color=mask_color)
                else:
                    single_cell = Cell(self.CELL_SIZE, self.image, cell_image, self.description, props, clear_cell=True)

                self.structure.append(single_cell)

                cell_address = (palette, element_id, cell_index, [])
                structure_map_row.append(cell_address)

                cell_index += 1

            self.structure_map.append(structure_map_row)

        return True

    def get_structure_map(self):
        """ Mapping the indexes of the elements,
            pointing to this object and its cells in the ImgLibrary.cellular_images list.
            Used into the MapEditor, when clicking the tool button to create an object.
        """
        if self.success:
            return self.structure_map

        return None


class BioImageUnit:
    def __init__(self, ref_id, library_name, image_filename:str, image_data:dict):

        self.id = ref_id
        self.library = library_name
        # self.cell_size = MapSettings.CELL_SIZE

        self.image = None
        self.mask = None

        self.width = None
        self.height = None

        self.animation = None

        self.description = None
        self.default_props = None
        # Note: image unit keeps a default properties (temperature, passable, resistance...).
        # In the biosphere units, that has copy of this props, they are chaged over time, individually.

        self.success = self.create(image_filename, image_data)


    def create(self, image_filename:str, image_data:dict):
        # image_props are stored in the json file associated with the image key_feature in its name.
        # Note: The images should be a multiple of cell_size.
        # TODO: add validation for that.
        try:
            if image_data["animated"]:
                frame_count = image_data["frame-count"]
                self.width = image_data["frame-width"]
                self.height = image_data["frame-height"]

                anim_speed = image_data["animation-speed"]
                self.animation = Animation(image_filename, self.width, self.height, frame_count, anim_speed)

                # -load the base image and the mask for collision detection:
                self.image = self.animation.get_frame(0)
                self.mask = pg.mask.from_surface(self.image)

            else:
                # self.animation = None
                self.image = pg.image.load(image_filename).convert()
                # self.width, self.height = self.image.get_size()
                self.width = image_data["frame-width"]
                self.height = image_data["frame-height"]

                self.image.set_colorkey(clr.WHITE)
                self.mask = pg.mask.from_surface(self.image)

            self.default_props = image_data["props"]
            self.description = image_data["description"]

            print(f"New Biolife image created successfully with properties: ")
            return True

        except Exception as e:
            print(f" Error while creating the BioImageUnit with id={self.id} [{image_filename}]: {e}")
            return False


class ImgLibrary:
    """Loading and indexing all the used images...
    """
    def __init__(self):
        self.cell_size = MapSettings.CELL_SIZE

        # --> Have the clear cell by hand, to be used in the map:
        self.clear_cell = self.create_clear_cell()

        # -- KEEPS ALL TYPES of CELL-BASED IMAGES
        # format: {"Palette0": [MpaCell0, MapCell1...], "Palette1": [MapCell0, MapCell1...]...}
        self.cellular_images = {}
        for key_feature in files.CELLULAR_TYPES:
            result = self.load_cellular_images(key_feature)
            print(result)
            # NOTE: when new key_library is created, its key_feature should be added to files.CELLULAR_TYPES.


        # 4. Load biolife images. Same format as cellular_images:
        # TODO: ---> REMOVE THIS
        # self.biolife_images = []
        # self.biolife_editor_list = {}  # contains "palette-name":[{"button_image":image, "reff-id":int}]
        # for key_feature in files.BIOLIFE_TYPES:
        #     result = self.load_biolife_images(key_feature)
        #     print(result)
        #     # NOTE: when new key_library is created, its key_feature should be added to files.CELLULAR_TYPES.

        # New version of loading biolife_images:
        self.biolife_images = {}
        for key_feature in files.BIOLIFE_TYPES:
            result = self.load_biolife_images_v2(key_feature)
            print(result)


        # Interface images for the editor buttons and other. Accessed via image_key ("tool-clicked")
        self.editor_images = self.load_editor_interface_images()

    def load_editor_interface_images(self):
        img_db = {}
        img_path = files.EDITOR_IMAGES

        # images are saved in img_db dict, as 'keys' (extracted from their names) and pg.image objects
        img_names_list = []
        for filename in os.listdir(img_path):
            if filename.endswith('.png'):
                image = pg.image.load(img_path + filename).convert()
                image.set_colorkey(clr.WHITE)
                file_id = os.path.splitext(filename)[0]
                img_db[file_id] = image

                # note: used for the final print info only
                img_names_list.append(file_id)

        # info_txt = ', '.join(img_names_list)
        print(f"Total of {len(img_names_list)} loaded: {img_names_list}")

        return img_db

    @staticmethod
    def create_clear_cell():
        clear_unit_data = {
            "description": "Empty cell unit...",
            "shape": [1, 1],
            "props": [
                {"passable": 1, "resistance": 0, "temp": 0, "risk": 0},
            ],
            "animated": 0
        }
        clear_cell = CellularImageUnit(element_id=0, palette=None, filename=files.CLEAR_CELL, unit_data=clear_unit_data)
        if clear_cell.success:
            return clear_cell
        else:
            print("Failed to create the clear cell unit.")
        return None

    def load_cellular_images(self, key_feature):
        """Version 2. Loads all types of images from """
        img_path = files.CELL_IMAGES

        # -->1. Loading the settings file for 'key_feature':
        try:
            img_data_file = os.path.join(img_path, f"{key_feature}.json")
            with open(img_data_file, 'r') as file:
                json_string = file.read()

                # Loads the json file
                data_list = json.loads(json_string)
                print(f"CellularImages props for {key_feature} loaded successfully")

        except FileExistsError:
            err = f"Cellular: Elements props {key_feature}.json file not found"
            return err

        # -->2. Get the files we're interested in (based on 'key_feature'):
        filename_list = []
        for filename in os.listdir(img_path):
            if key_feature in filename and filename.endswith('.png'):
                filename_list.append(filename)

        # -->3. Sort the filename_list:
        filenames_sorted = sorted(filename_list, key=lambda x: int(x.split('-')[-1].split('.')[0]))
        # Note: the lambda function split the filename 'map-rock-1.png' by "-", take the last element,
        # and split by '.' to take the part without .png. Then convert it to integer and use it for the sort.
        if not filenames_sorted:
            return f"Filenames listing FAILED, or no files associated with {key_feature}."

        # --4. Place a clear cell as a first element of the library on every palette:
        clear_cell = self.create_clear_cell()
        if clear_cell is not None:
            self.cellular_images[key_feature] = [clear_cell]
        else:
            return f"Failed to create the clear cell unit."

        # -->5. Next, create the rest of CellularUnits, using the sorted filenames list
        for i, filename in enumerate(filenames_sorted):
            full_filename = os.path.join(img_path, filename)
            cellular_unit = CellularImageUnit(i+1, key_feature, full_filename, data_list[i])
            if cellular_unit.success:
                self.cellular_images[key_feature].append(cellular_unit)
            else:
                return f"Failed to fill the ImageLibrary list for '{key_feature}'. Err in '{filename}' file."

        return f"All type [{key_feature}] cellular images loaded successfully."

    def load_biolife_images_v2(self, key_feature):
        result = False

        img_path = files.BIO_IMAGES

        # -->1. Loading the settings file for 'key_feature':
        try:
            img_data_file = os.path.join(img_path, f"{key_feature}.json")
            with open(img_data_file, 'r') as file:
                json_string = file.read()

                # Loads the json file
                data_list = json.loads(json_string)
                print(f"BioLife mage properties for {key_feature} loaded successfully.")

        except FileExistsError:
            err = f"BioLife: elements props {key_feature}.json file not found"
            return err

        # -->2. Get the files we're interested in (based on 'key_feature'):
        filename_list = []
        for filename in os.listdir(img_path):
            if key_feature in filename and filename.endswith('.png'):
                filename_list.append(filename)

        # -->3. Sort the filename_list:
        filenames_sorted = sorted(filename_list, key=lambda x: int(x.split('-')[-1].split('.')[0]))
        # Note: the lambda function split the filename 'map-rock-1.png' by "-", take the last element,
        # and split by '.' to take the part without .png. Then convert it to integer and use it for the sort.
        if not filenames_sorted:
            return f"Filenames listing FAILED, or no files associated with {key_feature}."

        # 3. Follow the sorted filename list to load the images in order:
        self.biolife_images[key_feature] = []
        for ref_id, filename in enumerate(filenames_sorted):
            full_filename = os.path.join(img_path, filename)
            image_data = data_list[ref_id]
            bioimage_unit = BioImageUnit(ref_id=ref_id,
                                         library_name=key_feature,
                                         image_filename=full_filename,
                                         image_data=image_data)
            if bioimage_unit.success:
                self.biolife_images[key_feature].append(bioimage_unit)
            else:
                return f"Failed to fill the BioImages list for '{key_feature}'. Err in '{filename}' file."

        return f"All type [{key_feature}] biolife images loaded successfully."




"""
Note for Img loading:
in the json file there is img-id, 
telling which is the image file for the each props.
"""

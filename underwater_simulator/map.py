import random
import textwrap
import json

from math import ceil

import pygame
import pygame as pg

from settings import MapSettings, ColorPalette as clr
from dbase import ImgLibrary

from typing import List


"""Everything placed and working on the map-structure cells is managed here,
    including rocks, plants, thermal vents, etc.
"""


class Map:

    def __init__(self, engine):
        self.engine = engine

        self.cell_size = MapSettings.CELL_SIZE

        self.cells_x = MapSettings.CELLS_X
        self.cells_y = MapSettings.CELLS_Y

        self.width = self.cells_x * self.cell_size
        self.height = self.cells_y * self.cell_size

        self.map_structure = self.new_map(MapSettings.CELLS_X, MapSettings.CELLS_Y)

    @staticmethod
    def new_map(cells_x, cells_y):
        line_len = 0
        map_structure = []
        for _ in range(cells_y):
            # line = [(None, 0, 0) for _ in range(cells_x)]
            line = [(None, 0, 0, []) for _ in range(cells_x)]
            line_len = len(line)
            # format: (key_feature, library_unit_index, unit_cell_index). key_feature='None' will put clear cell
            map_structure.append(line)

        print(f"New EMPTY MAP generated, {cells_x} x {cells_y} ({line_len} x {len(map_structure)}) -> last_element = {map_structure[-1][-1]} cells.")
        return map_structure

    def save_to_file(self, file_to_save):
        try:
            with open(file_to_save, 'w') as file:
                json.dump(self.map_structure, file)
                return f"Map Saved successfully in {file_to_save}"

        except Exception as e:
            return f"Map save FAILED: {e}"

    def load_from_file(self, file_to_load):
        try:
            with open(file_to_load, 'r') as file:
                self.engine.map.map_structure = json.load(file)

                # For testing purpouses only:
                # found_lifes = []
                # for row in range(self.cells_y):
                #     for col in range(self.cells_x):
                #         if self.engine.map.map_structure[row][col][3]:
                #             found_lifes.append(self.engine.map.map_structure[row][col][3])
                # print(found_lifes)

                return "Map structure Loaded successfully."

        except Exception as e:
            return f"Loading Map from file FAILED: {e}"

    def get_cell_property(self, map_coords: tuple, property_name: str):
        """ Returns a specific attribute from the units stored in the ImgLibrary.celular_images
            In the map_coords (x, y of the map matrix) we get the "address" of the object,
            written as tuple (key_feature, unit_id, cell_id), and finds what we are looking for...
        """
        # finds the element from the map_elements, with index (i, j) and return its property

        # - index validation...
        # print(tile_index)
        cell_index, row_index = map_coords

        if 0 <= row_index < self.cells_y:
            if 0 <= cell_index < self.cells_x:
                # creates a list of life_unit references if any life unit populates the cell:

                if property_name == "population":
                    return [self.engine.biolife.life_list[life_index] for life_index in self.map_structure[row_index][cell_index][3]]

                # 1. get the element:
                # cell_index format: ("map-rock", 18, 9)
                library_coords = self.map_structure[row_index][cell_index]
                # print(f"Getting property for {library_coords}")
                if library_coords[0] is not None:
                    palette_key = library_coords[0]
                    unit_id = library_coords[1]
                    cell_id = library_coords[2]
                    cell_object = self.engine.image_library.cellular_images[palette_key][unit_id].structure[cell_id]
                else:
                    cell_object = self.engine.image_library.clear_cell.structure[0]

                # 2. return the desired property:
                valid_props = {
                    "image": cell_object.image,
                    "base-img": cell_object.base_image,
                    "mask": cell_object.mask,
                    "props": cell_object.props,
                    "description": cell_object.description,
                }


                if property_name in valid_props.keys():
                    return valid_props[property_name]

        return None

    def draw(self):
        # Note: Drawing only the cells, located in the screen area. This should optimize the code...

        # 1. get the cells range only covered the screen:
        start_row_index = int(self.engine.scroll_y // self.cell_size)
        start_cell_index = int(self.engine.scroll_x // self.cell_size)
        end_row_index = int((self.engine.scroll_y + self.engine.height) // self.cell_size)
        end_cell_index = int((self.engine.scroll_x + self.engine.width) // self.cell_size)

        if end_row_index >= self.cells_y - 1:
            end_row_index = self.cells_y - 1

        if end_cell_index >= self.cells_x - 1:
            end_cell_index = self.cells_x - 1

        for row_index in range(start_row_index, end_row_index + 1):
            for cell_index in range(start_cell_index, end_cell_index + 1):
                # img_library_coordinates = self.map_structure[row_index][cell_index]  # ("map-rock", 18, 0)
                # cell_index is on 'x-axis', row_index is on 'y-axis'
                cell_img = self.get_cell_property((cell_index, row_index), "image")
                if cell_img is not None:
                    cell_pos_x = (cell_index * self.cell_size) - self.engine.scroll_x
                    cell_pos_y = (row_index * self.cell_size) - self.engine.scroll_y
                    self.engine.display.blit(cell_img, (cell_pos_x, cell_pos_y))

    def update(self, display_parameters):
        ...


class EditorPanel:
    """ Multipurpouse editor class to be used for Biolife editor and for Map editor too.
    """

    BORDER = 5  # px of outline border
    BTN_DISTANCE = 10  # px between the tool buttons
    BORDER_RADIUS = 10

    DRAG_AREA_HEIGHT = 40
    DRAG_RECT_HEIGHT = 25
    MAIN_MENU_HEIGHT = 50

    COLOR_ALPHA = (255, 255, 255)
    # COLOR_SILVER = (105, 106, 106)

    TERMINAL_HEIGHT = 120
    TERMINAL_COLOR = (50, 60, 57)
    TERMINAL_FONT_COLOR = (203, 219, 252)

    PANEL_BG_COLOR = (105, 106, 106)
    PANEL_DRAG_COLOR = (122, 116, 125)

    FONT_COLOR_MAIN = (155, 173, 183)
    FONT_COLOR_MENU = (203, 219, 252)
    FONT_COLOR_ACTIVE = (153, 229, 80)

    FONT_SIZE_MAIN = 12

    def __init__(self, panel_name, tool_btn_size, tools_per_row, main_menu_labels):
        self.panel_name = panel_name

        # properties (constant)
        self.tool_btn_size = tool_btn_size
        self.tools_per_row = tools_per_row if tools_per_row > 0 else 0

        # settings (changable)
        self.panel_width = (2 * self.BORDER) + (self.BTN_DISTANCE * tools_per_row-1) + (self.tool_btn_size*tools_per_row)
        self.panel_height = 100

        self.topleft = (100, 100)

        self.panel = None  # The panel surface, containing everything. Created every time a new palette is loaded

        self.button_borders = []  # a list of borders coresponding to the tool_buttons count.
        # Used to create a button clicked visual effect. Need to have on every button from the palette.

        # Main Menu:
        self.main_menu_labels = main_menu_labels
        self.main_menu_elements = []  # Keeps the menu surfaces and rects with their positions, to use in click check
        self.main_menu_top = 0
        self.main_menu_left = 0
        self.main_menu_width = 0
        self.main_menu_height = 0

        # terminal:
        self.TERMINAL_WIDTH = self.panel_width - 2 * self.BORDER
        self.terminal_font = pg.font.Font("freesansbold.ttf", self.FONT_SIZE_MAIN)
        self.terminal_text = "..."
        self.terminal_rect = None
        # Note: The text is drawn splited on lines, based of the panel_terminal width

        # If not active (visible), load and save functions wont work.
        self.active = False
        self.drag = False  # when mouse is down, the flag goes to True (see 'check_for_events()' in main.py.
        self.mouse_delta = (0, 0)  # when drag is activated, the position of mouse relative to panel topleft is saved.

        self.selected_tool = None

    def __resize_button(self, btn_image, new_size:int):
        if btn_image is not None:
            width = btn_image.get_width()
            if width != new_size:
                resized_img = pg.transform.scale(btn_image, (new_size, new_size))
            else:
                resized_img = btn_image.copy()

            resized_img.convert()
            resized_img.set_colorkey(self.COLOR_ALPHA)

            return resized_img

        return None

    def calculate_panel_height(self, tools_count):
        """Called to calculate new height, when a new palette is loaded, or a palette changes.
        """
        # by default the panel height will be for 3 rows of buttons:
        if tools_count <= 3 * self.tools_per_row:
            height = self.DRAG_AREA_HEIGHT + 5 + self.MAIN_MENU_HEIGHT + 10 + (4 * (self.tool_btn_size + self.BTN_DISTANCE) )+ self.TERMINAL_HEIGHT
        else:
            height = self.DRAG_AREA_HEIGHT + 5 + self.MAIN_MENU_HEIGHT + 10 + ((tools_count // self.tools_per_row)+1) * (self.tool_btn_size + self.BTN_DISTANCE) + self.TERMINAL_HEIGHT

        return height

    def reload_panel(self, tools_count, palette_key:str):
        """creates / rewrites the panel surface
            - palette_id is used to color the selected menu element and to draw text label on top of screen
            - tools_coint used for calculating panel_height
        """

        # 1. Calculate the panel height, needed for all buttons from the selected palette:
        self.panel_height = self.calculate_panel_height(tools_count)

        # 2. Creating the panel surface, based of the tools count:
        self.panel = pg.Surface((self.panel_width, self.panel_height))
        self.panel.fill(self.COLOR_ALPHA)

        # 3. Draw the main rectangle with rounded borders and background color:
        pg.draw.rect(self.panel, self.PANEL_BG_COLOR, (0, 0, self.panel_width, self.panel_height), border_radius=10)

        # 4. Draw colored rect on top of the panel to show the area where it can drag & draw:
        pg.draw.rect(self.panel, self.PANEL_DRAG_COLOR, (5, 5, self.panel_width-10, self.DRAG_RECT_HEIGHT), border_radius= 6)


        # 5. Put a label on the top
        label_font = pg.font.Font("freesansbold.ttf", self.FONT_SIZE_MAIN+2)
        label_text = f"{self.panel_name}: {palette_key}"
        label_surface = label_font.render(label_text, False, self.TERMINAL_COLOR)
        label_rect = label_surface.get_rect()
        label_rect.center = (self.panel_width // 2, 16)
        self.panel.blit(label_surface, label_rect)

        # 6. Converting and setting the color_key to remove the white background:
        self.panel.convert()
        self.panel.set_colorkey(self.COLOR_ALPHA)
        # Note: The top label will become transparent

        # 7. Generate Main Menu:
        menu_font = pg.font.Font("freesansbold.ttf", self.FONT_SIZE_MAIN)
        self.main_menu_top = self.DRAG_AREA_HEIGHT
        self.main_menu_elements.clear()
        for menu_label in self.main_menu_labels:
            # Note main_menu_list is a list of strings.
            # -check for active element and change its color:
            if menu_label == palette_key:
                menu_element_surface = menu_font.render(menu_label, True, self.FONT_COLOR_ACTIVE)
                is_active = True
            else:
                menu_element_surface = menu_font.render(menu_label, True, self.FONT_COLOR_MAIN)
                is_active = False

            menu_element_rect = menu_element_surface.get_rect()
            menu_element_rect.top = self.main_menu_top
            # menu_element_rect.left = self.BORDER + (i * menu_element_rect.width)
            menu_item = {
                "label": menu_label,
                "active": is_active,
                "surface": menu_element_surface,
                "rect": menu_element_rect
            }
            self.main_menu_elements.append(menu_item)

        # 8. position and draw main menu elements at the center of panel:
        self.main_menu_width = (len(self.main_menu_elements) * 15) - 15
        for element in self.main_menu_elements:
            self.main_menu_width += element["rect"].width
        self.main_menu_left = (self.panel_width - self.main_menu_width) // 2

        top_btm_border_size = 3
        for i, element in enumerate(self.main_menu_elements):
            if i == 0:
                element["rect"].left = self.main_menu_left
            else:
                element["rect"].left = self.main_menu_elements[i-1]["rect"].right + 10 + 5

            self.panel.blit(element["surface"], element["rect"])
            pg.draw.rect(self.panel, self.FONT_COLOR_MAIN, (element["rect"].left-5, element["rect"].top-top_btm_border_size, element["rect"].width+10, element["rect"].height+(2*top_btm_border_size)), 1)
        # Note: Now all the rects positions are changed and can be used for mouse_click check.
        self.main_menu_height = self.FONT_SIZE_MAIN + (2*top_btm_border_size)


        # 9. Drawing the terminal at the bottom of the panel:
        self.terminal_rect = pg.Rect(0, 0, self.TERMINAL_WIDTH, self.TERMINAL_HEIGHT)
        self.terminal_rect.left = self.BORDER
        self.terminal_rect.bottom = self.panel_height - self.BORDER
        pg.draw.rect(
            self.panel,
            self.TERMINAL_COLOR,
            self.terminal_rect,
            border_radius=6
        )

        self.print_to_terminal(f"Active Palette: {palette_key}")

    def close_panel(self):
        self.active = False
        self.selected_tool = None

    def main_menu_onclick(self, mouse):
        """Returns the menu element id if the mouse pointer is on an element
        """
        mouse_x, mouse_y = mouse

        menu_left = self.topleft[0] + self.main_menu_left
        menu_right = menu_left + self.main_menu_width
        menu_top = self.topleft[1] + self.main_menu_top
        menu_bottom = menu_top + self.main_menu_height

        if (menu_left < mouse_x < menu_right) and (menu_top < mouse_y < menu_bottom):
            # If in the menu area, check to match the button and return its index:
            for i, elem in enumerate(self.main_menu_elements):
                e_rect = elem["rect"]
                if (e_rect.left+self.topleft[0]) < mouse_x < (e_rect.right + self.topleft[0]) :
                    return elem["label"]
        return None

    def change_drag_drop_state(self, mouse_pos, mouse_down=False):
        if self.topleft[0] < mouse_pos[0] < (self.topleft[0]+self.panel_width):
            if self.topleft[1] < mouse_pos[1] < (self.topleft[1] + 30):
                if not self.drag and mouse_down:
                    self.drag = True

                    mouse_delta_x = mouse_pos[0] - self.topleft[0]
                    mouse_delta_y = mouse_pos[1] - self.topleft[1]
                    self.mouse_delta = (mouse_delta_x, mouse_delta_y)
                else:
                    self.drag = False
                    self.mouse_delta = (0, 0)
            else:
                self.drag = False
                self.mouse_delta = (0, 0)
        else:
            self.drag = False
            self.mouse_delta = (0, 0)

    def drag_drop(self):
        # the part for drag and drop is only the top line 30px thick:
        if self.active and self.drag:
            mouse_pos = pg.mouse.get_pos()
            # change the panel position with every mouse position:
            self.topleft = (mouse_pos[0]-self.mouse_delta[0], mouse_pos[1]-self.mouse_delta[1])

    def on_click_navigate(self, mouse):
        if self.active:
            # 1. Check for menu click and return the name of clicked library:
            result = self.main_menu_onclick(mouse)
            if result is not None:
                # result contains the string-id of the menu, so the palette will be easily selected:
                self.load_tool_palette(palette_key=result)

            # 3. Check for pick_place_tool
            self.pick_place_tool(mouse)

    def load_tool_palette(self, palette_key):
        # Note: this method is overwritten from the child classes
        ...

    def pick_place_tool(self, mouse):
        # Note: this method is overwritten from the child classes.
        ...

    def unselect_tool(self):
        if self.active:
            self.selected_tool = None
            self.clear_terminal()

    def clear_terminal(self):
        pg.draw.rect(
            self.panel,
            self.TERMINAL_COLOR,
            self.terminal_rect,
            border_radius=6
        )
        self.terminal_text = "..."

    def print_to_terminal(self, text_to_print:str = None, lines_to_print:list = None):
        """If text to print is given, it prints the text.
            If list of text is given, it prints them in separate lines.
        """
        # Note: Prints only when text_to_print or lines_to_print is not the same as the previous print:
        if text_to_print and not lines_to_print and text_to_print != self.terminal_text:
            self.clear_terminal()
            self.terminal_text = text_to_print

            # split the text line into lines to fit the terminal width:
            lines = textwrap.wrap(text_to_print, width=self.TERMINAL_WIDTH * 2 // self.FONT_SIZE_MAIN)

            # Render each line onto the surface
            # Note: text is rendered from 10,10 px topleft.
            x, y = (10, 10)
            panel_pos_y = self.panel_height - y - self.TERMINAL_HEIGHT
            for line in lines:
                rendered_text = self.terminal_font.render(line, True, self.TERMINAL_FONT_COLOR)
                self.panel.blit(rendered_text, (x, y + panel_pos_y))
                y += self.FONT_SIZE_MAIN

        elif lines_to_print and not text_to_print and lines_to_print != self.terminal_text:
            self.clear_terminal()
            self.terminal_text = lines_to_print.copy()

            x, y = (10, 10)
            panel_pos_y = self.panel_height - y - self.TERMINAL_HEIGHT
            for line in lines_to_print:
                rendered_text = self.terminal_font.render(line, True, self.TERMINAL_FONT_COLOR)
                self.panel.blit(rendered_text, (x, y + panel_pos_y))
                y += self.FONT_SIZE_MAIN


class MapEditorButton:
    def __init__(self, topleft:tuple, button_size:int, image_unit_refference, editor_images):

        self.frame_btn_up = self.resize_frame(editor_images['tool-notclicked'], button_size)
        self.frame_btn_down = self.resize_frame(editor_images['tool-clicked'], button_size)
        # self.btn_delete = editor_images['clear-unit']

        self.topleft = topleft

        self.image_unit = image_unit_refference

        self.tool_image = image_unit_refference.image

        self.width = button_size
        self.height = button_size
        self.button_image, self.button_rect = self.create_button_image(self.tool_image)

        # Used to assign the addresses from the structure_map to the map cells, when placing the objects.
        # format: [[("map-rock", 18,0),("map-rock", 18,1)],[("map-rock", 18,2),("map-rock", 18,3)]]

        self.structure_map = self.image_unit.get_structure_map()

        self.btn_down = False

    def create_button_image(self, tool_image):
        target_width = self.width
        target_height = self.height
        button_image = pg.surface.Surface((self.width, self.height))
        button_image.convert()
        button_image.fill(clr.WHITE)

        tool_img_width, tool_img_height = tool_image.get_size()
        aspect_ratio = tool_img_width / tool_img_height
        if aspect_ratio >= 1:
            scaled_width = target_width
            scaled_height = int(target_width / aspect_ratio)
        else:
            scaled_width = int(target_height * aspect_ratio)
            scaled_height = target_height

        scaled_image = pygame.transform.scale(tool_image, (scaled_width, scaled_height))
        # tool_button_img.convert()
        # tool_button_img.set_colorkey((0, 0, 0))

        scaled_image_rect = scaled_image.get_rect()  # used to center the image inside the rect of the button
        button_rect = button_image.get_rect()
        scaled_image_rect.center = button_rect.center

        # - drawing the image inside the button surface:
        button_image.blit(scaled_image, scaled_image_rect)
        button_image.set_colorkey(clr.WHITE)
        button_rect.topleft = self.topleft

        return button_image, button_rect

    @staticmethod
    def resize_frame(frame_image, button_size):
        if frame_image.get_width() == button_size:
            return frame_image
        else:
            return pygame.transform.scale(frame_image, (button_size,  button_size))


    def draw(self, panel):
        panel.blit(self.button_image, self.button_rect)
        if self.btn_down:
            panel.blit(self.frame_btn_down, self.button_rect)
        else:
            panel.blit(self.frame_btn_up, self.button_rect)


class MapEditor(EditorPanel):
    """ Used to create a cellular elements.
        - All map elements are positioned in the map matrix.
        - The cell can have only one cellular element at a time.
        - The cell value, pointing to the ImageLibrary is tuple = (key_feature:str, unit_id:int, cell_id:int)
        - key_feature points to the library in the dictionary ("map-rock", ...)
        - unit_id points to the unit in the "map-rock" or other list,
        - while "cell_id" points to the element in the unit.structure list.
        - Eventually map renders the image in the cell_id element.
    """

    TOOLS_PER_ROW = 6
    TOOL_BTN_SIZE = 32

    TOOLPANEL_TOP_CORRECTION = -10

    FILE_TO_SAVE = 'save/map-data.json'

    def __init__(self, engine):
        self.engine = engine

        # 2. Create a main menu for every type of cellular element
        main_menu_labels = list(engine.image_library.cellular_images.keys())
        print(main_menu_labels)

        super().__init__(
            panel_name="Map Cells Editor",
            tool_btn_size=self.TOOL_BTN_SIZE,
            tools_per_row=self.TOOLS_PER_ROW,
            main_menu_labels=main_menu_labels
        )

        # 3. Create a library of all tool_buttons, sorted by 'key_feature':
        self.tools_library = self.create_tools_library()

        # 4. Select the first library by default:
        self.selected_key:str = main_menu_labels[0]

        self.loaded_palette:List[MapEditorButton] = self.tools_library[self.selected_key]
        # Note: every time a palette is selected, the list is filled with buttons

        # 5. Create the panel, with size depending the tools count:
        tools_count = len(self.loaded_palette)
        self.reload_panel(tools_count, self.selected_key)

        # self.selected_tool = None
        # Note: self.selected_tool is moved to the parent class, so to become None when panel closes.

    def create_tools_library(self):
        tool_library = {}

        # 1. Loop in the ImgLibrary.cellular_images
        for key, palette_list in self.engine.image_library.cellular_images.items():
            tool_buttons_list = []

            # 2. Loop in every image palette and create a MapEditorButton instance
            # Note: Every button has it's location for placement on the EditorPanel.
            x = 0

            for i, cellular_unit in enumerate(palette_list):
                # 3. Calculate the position (top and left of the button
                # ---> TODO: calculate button position
                y = i // self.TOOLS_PER_ROW
                x = 0 if i % (self.TOOLS_PER_ROW) == 0 else x + 1

                left = 3+ self.BORDER + (x * (self.TOOL_BTN_SIZE + self.BTN_DISTANCE))
                top = self.BORDER + self.MAIN_MENU_HEIGHT + self.TOOLPANEL_TOP_CORRECTION + self.DRAG_AREA_HEIGHT + (y * (self.TOOL_BTN_SIZE + self.BTN_DISTANCE))
                topleft = (left, top)
                # Note: in Pygame module, rect.topleft is tuple with (x,y), so 'left' is first element, 'top' is second.

                button = MapEditorButton(topleft=topleft,
                                         button_size=self.TOOL_BTN_SIZE,
                                         image_unit_refference=cellular_unit,
                                         editor_images=self.engine.image_library.editor_images)

                tool_buttons_list.append(button)

            tool_library[key] = tool_buttons_list

        return tool_library

    def open_panel(self):
        tools_count = len(self.loaded_palette)
        self.reload_panel(tools_count, self.selected_key)
        self.active = True

    # Note: 'close_panel' method is located in the EditorPanel parent class.

    def load_tool_palette(self, palette_key):
        self.selected_key = palette_key
        self.loaded_palette = self.tools_library[palette_key]
        tools_count = len(self.loaded_palette)
        self.reload_panel(tools_count, palette_key)

    def pick_place_tool(self, mouse):
        # using write_coordinates_on map to put on map the data stored in the button.structure_map
        pos_x, pos_y = mouse

        toolbar_offset_x = self.BORDER
        toolbar_offset_y = self.DRAG_AREA_HEIGHT + self.main_menu_height + self.DRAG_AREA_HEIGHT + self.TOOLPANEL_TOP_CORRECTION

        # check if mouse position is in the area of tool_panel:
        if self.topleft[0] + self.BORDER < pos_x < self.topleft[0] + self.panel_width - self.BORDER:
            if self.topleft[1] + toolbar_offset_y < pos_y < self.topleft[1] + self.panel_height - self.BORDER:

                # get instrument ID:
                # Note: Calculating the index works faster than looping all the buttons and check for their topleft.
                tool_col = (pos_x - self.topleft[0] - toolbar_offset_x) // (self.TOOL_BTN_SIZE + self.BTN_DISTANCE)
                tool_row = (pos_y - self.topleft[1] - toolbar_offset_y) // (self.TOOL_BTN_SIZE + self.BTN_DISTANCE)

                tool_index = tool_col + tool_row * self.TOOLS_PER_ROW
                if 0 <= tool_index < len(self.loaded_palette):
                    self.selected_tool = self.loaded_palette[tool_index]
                    self.selected_tool.btn_down = True
                    self.print_tool_info()

                    return True

        # If function continue we check if clicked somewhere on the map, instead of the image:
        # And if there is a tool selected, place the tool on the map.
        if self.selected_tool is not None:
            self.write_on_map(mouse, self.selected_tool.structure_map)
            return True

        return False

    def write_on_map(self, mouse, structure_map):
        # Note: structure_map = None for BioLife 'self.selected_tool' shared attribute (see EditorPanel parent class).
        if structure_map is not None:
            pos_x, pos_y = mouse
            cell_col = (pos_x + self.engine.scroll_x) // MapSettings.CELL_SIZE
            cell_row = (pos_y + self.engine.scroll_y) // MapSettings.CELL_SIZE

            delta_row = 0
            delta_col = 0
            for row in structure_map:
                for unit_address in row:
                    self.engine.map.map_structure[int(cell_row + delta_row)][int(cell_col + delta_col)] = unit_address
                    # unit_address structure: ("map-rock", 18,0)
                    delta_col += 1
                delta_col = 0
                delta_row += 1

    def selected_button_up(self):
        if self.active and self.selected_tool is not None:
            self.selected_tool.btn_down = False

    def save_map(self):
        # when the key 's' pressed, and any editor_panel open, it saves all the map in file
        result = self.engine.map.save_to_file(self.FILE_TO_SAVE)
        print(result)
        if self.active:
            self.print_to_terminal(result)

    def load_map(self):
        # when the key 'o' is pressed and this or biolife panel is opened
        result = self.engine.map.load_from_file(self.FILE_TO_SAVE)
        print(result)
        if self.active:
            self.print_to_terminal(result)


    def mouse_draw(self, mouse):
        offset = (15, 15)
        if self.loaded_palette is not None and self.selected_tool is not None:
            mouse_image = self.selected_tool.tool_image
            self.engine.display.blit(mouse_image, (mouse[0]-offset[0], mouse[1]-offset[1]))

    def print_tool_info(self):
        if self.selected_tool is not None:
            info_lines = []
            info_lines.append(f"{self.selected_tool.image_unit.description} | ID = {self.selected_tool.image_unit.id}")
            info_lines.append(f"Shape: {self.selected_tool.image_unit.unit_data['shape']}")
            info_lines.append(f"Animated: {self.selected_tool.image_unit.unit_data['animated']}")

            self.print_to_terminal(lines_to_print=info_lines)

    def update(self):
        self.drag_drop()

    def draw_palette(self):
        for button in self.loaded_palette:
            button.draw(self.panel)
            # Note: Every button has its own draw method.
            # The method draws a border around the button, depending the "btn_down" state.

    def draw(self, mouse):
        if self.active:
            self.mouse_draw(mouse)
            self.engine.display.blit(self.panel, self.topleft)
            self.draw_palette()


# ================= BIOLIFE EDITOR: ======================

class BiolifeEditorButton:

    def __init__(self, topleft:tuple, button_size:int, bioimage_refference, editor_images, is_delete_button=False):
        self.frame_btn_up = self.resize_frame(editor_images['tool-notclicked'], button_size)
        self.frame_btn_down = self.resize_frame(editor_images['tool-clicked'], button_size)

        self.topleft = None

        self.image_unit = None
        # Note: if self.image_unit left None, it means this is a 'delete' button.

        # Used to display the unit image as a cursor
        self.tool_image = None

        self.width = None
        self.height = None

        # used to be a button image, resized to fit in 'button_size' rectangle:
        self.button_image, self.button_rect = None, None

        # Both are shared parameters used in parent EditorPanel class.
        # In BiolifeEditorButton, self.structure_map is left None.
        self.structure_map = None
        self.btn_down = False

        is_error = self.create(
            topleft=topleft,
            button_size=button_size,
            bioimage_refference=bioimage_refference,
            editor_images=editor_images,
            is_delete_button=is_delete_button
        )
        if is_error is not None:
            print(is_error)

    def create(self, topleft:tuple, button_size:int, bioimage_refference, editor_images, is_delete_button):

        self.topleft = topleft
        self.width = button_size
        self.height = button_size

        try:
            if is_delete_button:
                # the button will be used for placing delete tool in the palette, to delete any biolife unit.
                self.tool_image = editor_images['clear-unit']
            else:
                self.image_unit = bioimage_refference
                self.tool_image = bioimage_refference.image

            self.button_image, self.button_rect = self.create_button_image(self.tool_image)

            return None

        except Exception as e:
            return f"Error ocured while creating a button: {e}"

    def create_button_image(self, tool_image):
        target_width = self.width
        target_height = self.height

        tool_img_width, tool_img_height = tool_image.get_size()
        if target_width == tool_img_width and target_height == tool_img_height:
            button_image = tool_image
            button_rect = button_image.get_rect()
        else:
            button_image = pg.surface.Surface((self.width, self.height))
            button_image.convert()
            button_image.fill(clr.WHITE)

            aspect_ratio = tool_img_width / tool_img_height
            if aspect_ratio >= 1:
                scaled_width = target_width
                scaled_height = int(target_width / aspect_ratio)
            else:
                scaled_width = int(target_height * aspect_ratio)
                scaled_height = target_height

            scaled_image = pygame.transform.scale(tool_image, (scaled_width, scaled_height))

            scaled_image_rect = scaled_image.get_rect()  # used to center the image inside the rect of the button
            button_rect = button_image.get_rect()
            scaled_image_rect.center = button_rect.center

            # - drawing the image inside the button surface:
            button_image.blit(scaled_image, scaled_image_rect)
            button_image.set_colorkey(clr.WHITE)

        button_rect.topleft = self.topleft

        return button_image, button_rect

    @staticmethod
    def resize_frame(frame_image, button_size):
        if frame_image.get_width() == button_size:
            return frame_image
        else:
            return pygame.transform.scale(frame_image, (button_size, button_size))

    def draw(self, panel):
        panel.blit(self.button_image, self.button_rect)
        if self.btn_down:
            panel.blit(self.frame_btn_down, self.button_rect)
        else:
            panel.blit(self.frame_btn_up, self.button_rect)


class BiolifeEditor(EditorPanel):
    """ Used to create a free floating living elements.
        - There may be units that cover each other (on the same position).
        - However, the static elements are positioned with the map-cells top-left.
    """

    TOOLS_PER_ROW = 3
    TOOL_BTN_SIZE = 64  # 64x64 pixels

    TOOLPANEL_TOP_CORRECTION = -10
    TOOLPANEL_LEFT_CORRECTION = 3

    FILE_TO_SAVE = 'save/biolife-data.json'

    def __init__(self, engine):
        self.engine = engine

        """
        What button does: 
        in <- ImageLibrary {"image", "mask", "animation", "description", "props"}
        out -> to BioLife {"ref-id", "top", "left"}
        """

        # 1. Loading the palettes list and creating the main manu (containing the palette names)
        main_menu_labels = list(engine.image_library.biolife_images.keys())
        print(main_menu_labels)

        # 2. Panel Initializion:
        super().__init__(
            panel_name="BioLife Editor",
            tool_btn_size=self.TOOL_BTN_SIZE,
            tools_per_row=self.TOOLS_PER_ROW,
            main_menu_labels=main_menu_labels
        )

        # 3. Create a library of all tool_buttons, sorted by 'key_feature':
        self.tools_library = self.create_tools_library()

        # 4. Select the first library by default:
        self.selected_key: str = main_menu_labels[0]

        self.loaded_palette: List[BiolifeEditorButton] = self.tools_library[self.selected_key]

        # 5. Create the panel, with size depending the tools count:
        tools_count = len(self.loaded_palette)
        self.reload_panel(tools_count, self.selected_key)

        self.selected_tool = None
        # it is a list of {"tool-image", "ref-id"}, stated under "bush"...

    def create_tools_library(self):
        tool_library = {}

        # 1. Loop in the ImgLibrary.biolife_images
        for key, palette_list in self.engine.image_library.biolife_images.items():

            # 2. Loop in every palette and create a BiolifeEditorButton instance
            # Note: Every button has it's location for placement on the EditorPanel, and draw method to draw it there.

            # Delete button is added to every library of buttons, at the beginitin, i=0.
            x, y = (0, 0)
            left = self.TOOLPANEL_LEFT_CORRECTION + self.BORDER + (x * (self.TOOL_BTN_SIZE + self.BTN_DISTANCE))
            top = self.BORDER + self.MAIN_MENU_HEIGHT + self.DRAG_AREA_HEIGHT + self.TOOLPANEL_TOP_CORRECTION + (y * (self.TOOL_BTN_SIZE + self.BTN_DISTANCE))

            topleft = (left, top)

            button = BiolifeEditorButton(topleft=topleft,
                                         button_size=self.TOOL_BTN_SIZE,
                                         bioimage_refference=None,
                                         editor_images=self.engine.image_library.editor_images,
                                         is_delete_button=True)

            tool_buttons_list = [button]

            for i, bioimage_unit in enumerate(palette_list):
                # 3. Calculate the position (top and left of the button
                y = (i+1) // self.TOOLS_PER_ROW
                x = 0 if (i+1) % self.TOOLS_PER_ROW == 0 else x+1

                left = self.TOOLPANEL_LEFT_CORRECTION + self.BORDER + (x * (self.TOOL_BTN_SIZE + self.BTN_DISTANCE))
                top = self.BORDER + self.MAIN_MENU_HEIGHT + self.DRAG_AREA_HEIGHT + self.TOOLPANEL_TOP_CORRECTION + (y*(self.TOOL_BTN_SIZE + self.BTN_DISTANCE))
                topleft = (left, top)
                # Note: in Pygame module, rect.topleft is tuple with (x,y), so 'left' is first element, 'top' is second.

                button = BiolifeEditorButton(topleft=topleft,
                                             button_size=self.TOOL_BTN_SIZE,
                                             bioimage_refference=bioimage_unit,
                                             editor_images=self.engine.image_library.editor_images)

                tool_buttons_list.append(button)

            tool_library[key] = tool_buttons_list

        return tool_library

    def open_panel(self):
        tools_count = len(self.loaded_palette)
        self.reload_panel(tools_count, self.selected_key)
        self.active = True

    def load_tool_palette(self, palette_key):
        self.selected_key = palette_key
        self.loaded_palette = self.tools_library[palette_key]
        tools_count = len(self.loaded_palette)
        self.reload_panel(tools_count, palette_key)

    def pick_place_tool(self, mouse):
        pos_x, pos_y = mouse

        toolbar_offset_x = self.BORDER
        toolbar_offset_y = self.DRAG_AREA_HEIGHT + self.main_menu_height + self.DRAG_AREA_HEIGHT + self.TOOLPANEL_TOP_CORRECTION

        # 1. Check if mouse position is in the area of tool_palette:
        if self.topleft[0] + self.BORDER < pos_x < self.topleft[0] + self.panel_width - self.BORDER:
            if self.topleft[1] + toolbar_offset_y < pos_y < self.topleft[1] + self.panel_height - self.BORDER:

                # 2. Get clicked button ID:
                tool_col = (pos_x - self.topleft[0] - toolbar_offset_x) // (self.TOOL_BTN_SIZE + self.BTN_DISTANCE)
                tool_row = (pos_y - self.topleft[1] - toolbar_offset_y) // (self.TOOL_BTN_SIZE + self.BTN_DISTANCE)
                tool_index = tool_col + tool_row * self.TOOLS_PER_ROW

                if 0 <= tool_index < len(self.loaded_palette):
                    # Note: this check is used because if the last row is not full,
                    # we still get index calculation after the last button, until the end of the row.
                    self.selected_tool = self.loaded_palette[tool_index]
                    self.selected_tool.btn_down = True
                    self.print_tool_info()

                    return True

        if self.selected_tool is not None:
            if self.selected_tool.image_unit is not None:
                # This is a valid instrument, pointing to image_unit in ImageLibrary
                result = self.engine.biolife.add_life_unit(self.selected_tool.image_unit.id,
                                                           self.selected_tool.image_unit.library,
                                                           mouse)
                if result is not None:
                    self.print_to_terminal(lines_to_print=result)

            else:
                # This is a delete unit. Use delete method from biosphere.py module
                result = self.engine.biolife.delete_life_unit(mouse)
                if result is not None:
                    # Note: result is 2 lines in list.
                    self.print_to_terminal(lines_to_print=result)

    def print_tool_info(self):
        if self.selected_tool is not None:
            info_lines = []
            if self.selected_tool.image_unit is not None:
                info_lines.append(f"{self.selected_tool.image_unit.description} | ID = {self.selected_tool.image_unit.id}")
                info_lines.append(f"Library: '{self.selected_tool.image_unit.library}'")
                if self.selected_tool.image_unit.animation is not None:
                    info_lines.append("Animated: False")
                else:
                    info_lines.append("Animated: False")

                for key, value in self.selected_tool.image_unit.default_props.items():
                    info_lines.append(f"  - {key}: {value}")

            else:
                info_lines.append("Delete Tool:")
                info_lines.append("Click on BioLife unit, to remove it...")

            self.print_to_terminal(lines_to_print=info_lines)

    def selected_button_up(self):
        if self.active and self.selected_tool is not None:
            self.selected_tool.btn_down = False

    def save_biolife(self):
        # when the key 's' is pressed
        result = self.engine.biolife.save_to_file(self.FILE_TO_SAVE)
        print(result)
        if self.active:
            self.print_to_terminal(result)

    def load_biolife(self):
        # when the key 'o' is pressed:
        result = self.engine.biolife.load_from_file(self.FILE_TO_SAVE)
        print(result)
        if self.active:
            self.print_to_terminal(result)

    def update(self):
        self.drag_drop()

    def draw_palette(self):
        for button in self.loaded_palette:
            button.draw(self.panel)
            # Note: Every button has its own draw method.
            # The method draws a border around the button, depending the "btn_down" state.

    def mouse_draw(self, mouse):
        if self.selected_tool is not None:
            offset = (15, 15)
            if self.loaded_palette is not None and self.selected_tool is not None:
                mouse_image = self.selected_tool.tool_image
                self.engine.display.blit(mouse_image, (mouse[0] - offset[0], mouse[1] - offset[1]))

    def draw(self, mouse):
        # Note: There will be no window transparancy, because it creates complexity in the code.
        if self.active:
            self.mouse_draw(mouse)
            self.engine.display.blit(self.panel, self.topleft)
            self.draw_palette()














import os
from sys import exit as sys_exit
import time
import psutil

import pygame as pg

import threading

from settings import ScreenSettings, EnvironmentProps, FileLocations as files, ColorPalette as clr
from dbase import ImgLibrary
from controller import JoyStick, HandWatch
from map import Map, MapEditor, BiolifeEditor
from interface import InfoService, Gauger, Pointer, Terminal

from submarine import Sub20

from biosphere import Water, Air, BioLife

# Fix the issue of pygame 'wayland not available'.
# If this does not fix, logout and login via x11 (Ubuntu on Xorg).
# os.environ['SDL_VIDEODRIVER'] = 'x11'


class Engine:
    """Care only for displaying the objects on the screen.
    """
    def __init__(self):
        pg.init()

        # -- display --
        monitor_size = (pg.display.Info().current_w, pg.display.Info().current_h)
        scale_factor = ScreenSettings.SCALE_FACTOR
        self.width = monitor_size[0] // scale_factor
        self.height = monitor_size[1] // scale_factor

        self.display = pg.display.set_mode((self.width, self.height), pg.FULLSCREEN)
        pg.display.set_caption(f"subColony v.0.7")

        self.scroll_x = 0
        self.scroll_y = 0
        self.scroll_speed = ScreenSettings.SCROLL_SPEED

        # -- image library --
        # It contains all the visual elements (pygame images)
        self.image_library = ImgLibrary()

        # -- controls --
        self.joystick = JoyStick()
        # self.mouse = Mouse(self)


        # -- map --
        self.map = Map(self)
        # self.mapeditor = MapEditor(self)
        self.mapeditor = MapEditor(self)
        self.biolife_editor = BiolifeEditor(self)

        # -- Ecosystem --
        self.seawater_deep = Water(self, EnvironmentProps.SEAWATER_DEEP, f"{files.WATER_IMAGES}water_deep.png", 1)
        self.seawater_shallow = Water(self, EnvironmentProps.SEAWATER_SHALLOW, f"{files.WATER_IMAGES}water_shallow.png", 2)

        # self.waters = [self.seawater_deep, self.seawater_shallow]
        # TODO: 1. Waters are initialized in order from TOP to BOTTOM
        # TODO: 2. The top water is the surface water used for Air initializing
        # TODO: 3. Collision of the submerged object is check with every water in the list
        # Note: shallow_water neet to be init before air, in order to use shallow-water mask.
        self.air = Air(self)

        # -- Biosphere --
        self.biolife = BioLife(self)


        # -- submarine --
        self.sub = Sub20(self)

        # -- interface --
        self.info_service = InfoService(self)

        self.last_info_update = pg.time.get_ticks()
        self.info_update_interval = 100

        self.gauger = Gauger(self)
        self.pointer = Pointer(self)

        self.terminal = Terminal(self)

        # -- system --
        self.system_info = ""
        self.system_temp = 0

        self.clock = pg.time.Clock()
        self.is_running = True

        self.thread = threading.Thread(target=self.get_system_info_thread)
        self.thread.start()

        self.mapeditor.load_map()
        self.biolife_editor.load_biolife()

        self.handwatch = HandWatch(self)

    def scroll(self, direction: tuple):
        """ Scroll the screen to a direction:
            (x, y), coming from the controller
        """
        if not direction == (0, 0):
            self.scroll_x += direction[0] * self.scroll_speed
            self.scroll_y += direction[1] * self.scroll_speed

            self.scroll_x = max(0, min(self.scroll_x, self.map.width - self.width))
            self.scroll_y = max(0, min(self.scroll_y, self.map.height - self.height))

    def auto_scroll(self):
        """ Auto Scroll in the map with the moving object.
            The moving object will always stay in the center of the screen.
        """
        self.scroll_x = self.sub.pos_x - self.width // 2
        self.scroll_y = self.sub.pos_y - self.height // 2

        self.scroll_x = max(0, min(self.scroll_x, self.map.width - self.width))
        self.scroll_y = max(0, min(self.scroll_y, self.map.height - self.height))


    def check_for_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.is_running = False

            if event.type in self.joystick.valid_events and self.joystick.success:
                self.joystick.event_decode(event)

            # -- mouse click --
            if event.type == pg.MOUSEBUTTONDOWN:
                """
                1 - left click
                2 - middle click
                3 - right click
                4 - scroll up
                5 - scroll down
                alternative: state = pygame.mouse.get_pressed()
                returns tupple: (leftclick, middleclick, rightclick)
                """

                mouse_pos = pg.mouse.get_pos()
                if event.button == 1:  # Left mouse button down
                    self.mapeditor.change_drag_drop_state(mouse_pos, True)  # Method in Editor_panel
                    self.mapeditor.on_click_navigate(mouse_pos)

                    self.biolife_editor.change_drag_drop_state(mouse_pos, True)
                    self.biolife_editor.on_click_navigate(mouse_pos)

                elif event.button == 3:
                    self.mapeditor.unselect_tool()
                    self.biolife_editor.unselect_tool()


            elif event.type == pg.MOUSEBUTTONUP:
                mouse_pos = pg.mouse.get_pos()
                if event.button == 1:  # Left mouse button down
                    self.mapeditor.change_drag_drop_state(mouse_pos)
                    self.mapeditor.selected_button_up()

                    self.biolife_editor.change_drag_drop_state(mouse_pos)
                    self.biolife_editor.selected_button_up()
                    ...
                elif event.button == 3:
                    # self.mouse.right_up(mouse_pos)
                    ...

            # -show/hide mapeditor tool pallette when pressing "m" button:
            if event.type == pg.KEYUP:
                if event.key == pg.K_m:
                    if self.mapeditor.active:
                        self.mapeditor.close_panel()
                    else:
                        self.mapeditor.open_panel()

                elif event.key == pg.K_b:
                    # Show / Hide BioLife Editor:
                    # TODO do this with props in biolife editor.
                    if self.biolife_editor.active:
                        self.biolife_editor.close_panel()
                    else:
                        self.biolife_editor.open_panel()

                elif event.key == pg.K_s:
                    # Note: save both files together. Important to keep life_unit indexes on track
                    if self.mapeditor.active or self.biolife_editor.active:
                        self.mapeditor.save_map()
                        self.biolife_editor.save_biolife()

                elif event.key == pg.K_o:
                    if self.mapeditor.active or self.biolife_editor.active:
                        self.mapeditor.load_map()
                        self.biolife_editor.load_biolife()

                elif event.key == pg.K_p:
                    self.pointer.active = not self.pointer.active

                elif event.key == pg.K_r:
                    self.sub.reset_position()

                elif event.key == pg.K_h:
                    self.handwatch.active = not self.handwatch.active

                # elif event.key == pg.K_z:
                #     self.biolife.map_correct()

    def get_system_info_thread(self):
        while self.is_running:
            self.system_temp = psutil.sensors_temperatures()['center_thermal'][0].current
            self.system_info = f"[{self.clock.get_fps():.1f} fps.] | CPU: {psutil.cpu_percent(interval=1):.1f} % | {self.system_temp:.2f} °C | MEMORY: {psutil.virtual_memory().percent:.1f} %"
            # print(self.system_info)
            self.info_service.update_item(0, self.system_info)

            time.sleep(1)

        print("System Info Thread stopped successfully.")

    # def update_sub_info_data(self):
    #     time_now = pg.time.get_ticks()
    #     if time_now - self.last_info_update > self.info_update_interval:
    #
    #         # text_data0 = f"Thruster: {self.sub.thrust_force:.2f} | Spray: {self.sub.spray_force:.2f} | Ballast: {self.sub.ballast_fill}% |  Buoyancy: {self.sub.buoyancy:.2f}"
    #         # self.info_service.update_item(1, text_data0)
    #
    #         text_data1 = f"Thrust-ON: {self.joystick.get_thruster_state()} | Spray-ON: {self.joystick.get_spray_state()} | AUTOSCROL: {self.joystick.autoscroll_on}"
    #         self.info_service.update_item(1, text_data1)
    #
    #         # self.info_service.update_item(3, self.sub.center_tile_data)
    #
    #         self.last_info_update = time_now

    def update(self):
        pg.display.flip()
        # dt = self.clock.tick() / 1000
        self.clock.tick(ScreenSettings.FPS)

        # pg.display.set_caption(f"subColony v.0.7")

        if self.joystick.success:
            if not self.joystick.autoscroll_on:
                self.scroll(self.joystick.scroll_direction)
            else:
                self.auto_scroll()
        else:
            # TODO: check if the keyboard controls turn on or off the autoscroll
            # If autoscroll is on,
            self.auto_scroll()
            # Note: TODO: it can be turned off from the keyboard

        self.mapeditor.drag_drop()

        self.biolife_editor.update()

        self.seawater_deep.update()
        self.seawater_shallow.update()
        self.air.update()

        self.biolife.update()

        self.sub.update()

        # self.update_sub_info_data()
        self.gauger.update()

        self.pointer.update()

        if self.handwatch.success and self.handwatch.active:
            self.handwatch.update()

        self.terminal.update()

    def draw(self):
        self.display.fill(clr.BLACK)

        self.seawater_shallow.draw()
        self.seawater_deep.draw()
        # self.air.debug_draw()

        self.map.draw()

        self.biolife.draw()

        self.sub.draw()
        # self.sub.visualize_interaction()

        self.info_service.draw()
        # self.info_service.draw_system_only()
        self.gauger.draw()

        mouse_pos = pg.mouse.get_pos()
        self.mapeditor.draw(mouse_pos)
        self.biolife_editor.draw(mouse_pos)

        # self.mapeditor.mouse_draw(mouse_pos)
        # self.biolife_editor.mouse_draw(mouse_pos)

        self.pointer.draw()

        self.handwatch.draw(self.display)

        self.terminal.draw()

    def run(self):
        while self.is_running:
            self.check_for_events()
            self.update()
            self.draw()

        if self.thread.is_alive():
            self.thread.join()

        self.handwatch.terminate()
        pg.quit()
        sys_exit()


if __name__ == '__main__':
    engine = Engine()
    engine.run()

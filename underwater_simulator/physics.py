import pygame as pg
import math
from statistics import mean

from typing import List
from tools import Tools

from settings import MapSettings, ColorPalette as clr

"""
Description:
The module is used to generate physical impact
between the surrounding environment and the unit.

The idea of using a separate module, is to give the Sub and every other moving unit
the same environmental impact, whether for collision or temperature/pressure/damage affect...

Note: This is used for generating physical impact to the unit in range 'surrounding_range'
"""


class ImpactCell:
    def __init__(self, map_coords:tuple, cell_mask: pg.mask.Mask, cell_props: dict, cell_population: list):
        self.map_coords = map_coords  # the cell coords on the map (col, row)
        self.mask = cell_mask
        self.props = cell_props
        self.population = cell_population

    @property
    def cell_topleft(self):
        left = self.map_coords[0] * MapSettings.CELL_SIZE
        top = self.map_coords[1] * MapSettings.CELL_SIZE
        return left, top


class Physics:

    def __init__(self, unit):
        # Reference to the unit that the impact applies.
        # NOTE: unit can be submarine, fish, monster, etc...
        # so make sure that the callings are to a shared methods only
        self.unit = unit
        self.next_rotated_mask = None
        self.next_rotated_rect = None

        # Used: engine,  center_cell_coords, pos_x, pos_y, center_mask, settings, image

        self.engine = self.unit.engine

        # Range of the environment, that physical affect is collected (cells, rows)
        self.range = unit.settings.PHYSICS_CHECK_RANGE

        # Note: TO get unit_center, simply get the 'self.unit.center_cell_coords property'.

        # --- Physics ---
        # Note: These attributes are used from the unit itself, instead of having its own:
        self.velocity = 0
        self.rotation_momentum = 0
        self.buoyancy_momentum = 0

        self.resistance_passable = 0
        self.resistance_nonpassable = 0

        self.cell_overlap = []
        self.life_overlap = {}

        self.surrounding_temp = 0
        self.surrounding_risk = 0

        # Depending of how much area is out of the water will be the solar and healing gain...
        # Updated from is_underwater() method
        self.out_of_water_area = 0

        self.another_mask_img = None

        self.air_overlap_point = None

    @property
    def impact_matrix(self) -> List[List[ImpactCell]]:
        """ Generates cells matrix with all cell data needed, in the given 'surrounding_range' """
        impact_matrix = []

        # 1. Get the start cell (top-left) index and end cell (bottom-right) index of the range:
        center_cell_index_x, center_cell_index_y = self.unit.center_cell_coords

        cell_start_index = center_cell_index_x - (self.range[0] // 2)
        if cell_start_index < 0:
            cell_start_index = 0

        cell_end_index = cell_start_index + self.range[0]
        if cell_end_index >= self.engine.map.cells_x - 1:
            cell_end_index = self.engine.map.cells_x - 1

        row_start_index = center_cell_index_y - (self.range[1] // 2)
        if row_start_index < 0:
            row_start_index = 0
        row_end_index = row_start_index + self.range[1]
        if row_end_index >= self.engine.map.cells_y - 1:
            row_end_index = self.engine.map.cells_y - 1

        # 2. Get all the cell's data and populate cells_list[] with CellImpact units:
        for row_index in range(row_start_index, row_end_index + 1):
            impact_row = []
            for cell_index in range(cell_start_index, cell_end_index + 1):
                # -get the cell's data:
                cell_coords = (cell_index, row_index)
                cell_mask = self.engine.map.get_cell_property(cell_coords, "mask")
                cell_props = self.engine.map.get_cell_property(cell_coords, "props")
                cell_population = self.engine.map.get_cell_property(cell_coords, "population")

                # -create the ImpactCell instance and append it to the matrix list
                impact_cell = ImpactCell(map_coords=cell_coords,
                                         cell_mask=cell_mask,
                                         cell_props=cell_props,
                                         cell_population=cell_population)
                impact_row.append(impact_cell)

            impact_matrix.append(impact_row)

        return impact_matrix

    @property
    def thermal_energy(self):
        # The property returns energy, depending the outside temperature
        result = 0  # Ranged from 0 to 1
        efficiency_coef = 1
        temp = self.surrounding_temp
        if 50 < temp < 200:
            result = Tools.range_value(temp, 50, 200, 0, 1)
            result = result * efficiency_coef
        return result

    @property
    def solar_energy(self):
        # The property returns energy, depending the depth. When on surface
        # Note: Sun Energy gain begins in shallow water.
        efficiency_coef = 0.5  # if the energy gain is max (which is =1), the total will be 1* efficiency_coef
        effect_of_water = 0.4  # when underwater, efficiency drops more than double.
        energy_gain = 0

        if self.unit.pos_y <= self.engine.seawater_shallow.total_depth + 200:  # note: +100 because of the deep water waves.

            out_of_water_percentage = self.unit.physics.out_of_water_area / self.unit.contour_area
            # Use the out_of_water_percentage parameter to rapidly increase solar energy gain when out of water...
            if out_of_water_percentage > 0:
                energy_gain = efficiency_coef * out_of_water_percentage

            max_up = self.engine.seawater_shallow.pos_y
            energy_gain += (max_up / self.unit.pos_y) * efficiency_coef * effect_of_water

            if energy_gain > 1:
                energy_gain = 1

        return energy_gain

    def get_matrix_coords(self) -> tuple:
        center_cell_index_x, center_cell_index_y = self.unit.center_cell_coords

        cell_start_index = center_cell_index_x - (self.range[0] // 2)
        if cell_start_index < 0:
            cell_start_index = 0

        cell_end_index = cell_start_index + self.range[0]
        if cell_end_index >= self.engine.map.cells_x - 1:
            cell_end_index = self.engine.map.cells_x - 1

        row_start_index = center_cell_index_y - (self.range[1] // 2)
        if row_start_index < 0:
            row_start_index = 0
        row_end_index = row_start_index + self.range[1]
        if row_end_index >= self.engine.map.cells_y - 1:
            row_end_index = self.engine.map.cells_y - 1

        return cell_start_index, row_start_index, cell_end_index, row_end_index

    def get_impact_cell(self, col, row) -> ImpactCell:
        cell_coords = (col, row)
        cell_mask = self.engine.map.get_cell_property(cell_coords, "mask")
        cell_props = self.engine.map.get_cell_property(cell_coords, "props")
        cell_population = self.engine.map.get_cell_property(cell_coords, "population")

        # -create the ImpactCell instance and append it to the matrix list
        impact_cell = ImpactCell(map_coords=cell_coords,
                                 cell_mask=cell_mask,
                                 cell_props=cell_props,
                                 cell_population=cell_population)
        return impact_cell

    def is_underwater(self, next_pos_x, next_pos_y):
        """Checks if the submarine's center is on the edge of surface_water and adjust its position accordingly
                """

        if self.unit.pos_y < self.engine.air.floating_check_start_from:
            """ Used for:
                - Check if center of the unit is underwater. For generating floating 
                - Check if unit's tail is out of water. In sub, this is used for communication.
                - Check if part of the unit is out of the water and calculate the area outside.
            """
            # 1. Get the air mask:
            air_mask = self.engine.air.mask
            air_mask_scroll = self.engine.air.scroll_x
            air_mask_top = self.engine.air.top


            # 2. First, check if any part of sub is out of water and caclulate out_of_water_area ...
            self.out_of_water_area = 0  # in number of pixels.

            large_air_mask = self.engine.air.large_mask
            large_air_height = self.engine.air.large_height
            large_top = self.engine.seawater_shallow.pos_y - large_air_height

            offset_x = self.next_rotated_rect.x - air_mask_scroll
            offset_y = self.next_rotated_rect.y - (large_top + 70)

            if self.next_rotated_mask is not None:
                mask_img = self.next_rotated_mask.to_surface(unsetcolor=(0,0,0,0))
                self.another_mask_img = mask_img

                self.out_of_water_area = large_air_mask.overlap_area(
                    self.next_rotated_mask,
                    (offset_x, offset_y)
                )

                # overlap_with_air = large_air_mask.overlap_mask(
                #     self.next_rotated_mask,
                #     (offset_x, offset_y)
                # )

                # self.air_overlap_point = air_mask.overlap(
                #     self.next_rotated_mask,
                #     (offset_x, offset_y1)
                # )

                # if overlap_with_air is not None:
                #     self.another_mask_img = overlap_with_air.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=(255, 255, 255, 255))


            # 3. TODO: check if unit's tail is out of water:
            if self.out_of_water_area:
                # TODO: Check if unit's tali mask is out of the water and update the method's return
                ...

            # 4. check if center_mask (the little circular mask located on unit's center is out of water...
            overlap = air_mask.overlap(
                self.unit.center_mask,
                (next_pos_x - air_mask_scroll, next_pos_y - air_mask_top)
            )
            if overlap:
                return False

        return True

    @staticmethod
    def check_off_map(next_pos_x, next_pos_y, map_width, map_height):
        """Check the position of the sub relative to the map edges
            and return the edges where the sub-center is about to go off-map
        """
        if next_pos_x < 0 or next_pos_x > map_width or next_pos_y < 0 or next_pos_y > map_height:
            return True
        return False

    def calculate_resistance_effect(self, thrust_force, spray_force, arg="passable"):
        if arg == "passable":
            resistance = self.resistance_passable
            # for passable objects, resistance depends on the force of mocvement:
            effect = Tools.calculate_total_force([abs(thrust_force), abs(spray_force)])

            return resistance * effect
        else:
            # if we need the resistance for non-passable objects, we return it directly.
            return self.resistance_nonpassable

    @staticmethod
    def calculate_velocity(current_momentum, thrust_force, resistance_effect, unit_mass, resolution):
        result = current_momentum

        force_direction = math.copysign(1, thrust_force)
        net_force = (thrust_force - (force_direction * resistance_effect)) * resolution

        effect_of_mass = 1 / unit_mass  # Note: decreasing this, will increase the time the velocity builds up
        # As heavier is the object, as slower the momentum will increase / decrease

        # TODO: the resistance_passable also causes an effect to the acceleration time. It should be applied.

        if result < net_force:
            result += effect_of_mass + effect_of_mass * abs(net_force)
        elif result > net_force:
            result -= (effect_of_mass + effect_of_mass * abs(net_force))

        if abs(result) < effect_of_mass and thrust_force == 0:
            result = 0

        # debug_info = f"net-force: {net_force:.2f} | result: {result:.2f}"
        # self.engine.info_service.update_item(2, debug_info)

        return result

    @staticmethod
    def calculate_rotation_momentum(current_momentum, spray_force, resistance_effect, unit_mass, resolution):
        result = current_momentum
        # Note: resolution is used to convert the rotation_momentum to degrees per frame.

        # net_force = (self.spray_force - (self.spray_force * self.resistance_passable)) * degrees_per_frame
        force_direction = math.copysign(1, spray_force)
        net_force = (spray_force - (force_direction * resistance_effect)) * resolution

        effect_of_mass = 1 / (2 * unit_mass)

        if result < net_force:
            result += effect_of_mass + effect_of_mass * abs(net_force)
        elif result > net_force:
            result -= effect_of_mass + effect_of_mass * abs(net_force)

        if abs(result) < effect_of_mass and spray_force == 0:
            result = 0

        return result

    @staticmethod
    def calculate_buoyancy_momentum(current_momentum, buoyancy, environment_resistance, resolution):
        result = current_momentum
        resistance_effect = 0.1 + environment_resistance / 10

        # without resistance applied:
        # if self.buoyancy_momentum < self.buoyancy:
        #     self.buoyancy_momentum += 0.1 + abs(self.buoyancy)
        # elif self.buoyancy_momentum > self.buoyancy:
        #     self.buoyancy_momentum -= 0.1 + abs(self.buoyancy)
        # if abs(self.buoyancy_momentum) < 0.1 and self.buoyancy == 0:
        #     self.buoyancy_momentum = 0

        # with resistance applied:
        # TODO: update this with resistance applied.
        if result < buoyancy:
            result += 0.1 + abs(buoyancy)
        elif result > buoyancy:
            result -= 0.1 + abs(buoyancy)

        if abs(result) < 0.1 and buoyancy == 0:
            result = 0

        return result

    def update(self, thrust_force, spray_force, buoyancy):
        unit_mass = self.unit.settings.MASS
        buoyancy_resolution = self.unit.settings.BUOYANCY_RESOLUTION
        speed_resolution = self.unit.settings.SPEED_RESOLUTION
        rotation_resolution = self.unit.settings.ROTATION_RESOLUTION

        resistance_effect = self.calculate_resistance_effect(
            thrust_force,
            spray_force,
        )

        self.velocity = self.calculate_velocity(
            current_momentum=self.velocity,
            thrust_force=thrust_force,
            resistance_effect=resistance_effect,
            unit_mass=unit_mass,
            resolution=speed_resolution
        )

        self.rotation_momentum = self.calculate_rotation_momentum(
            current_momentum=self.rotation_momentum,
            spray_force=spray_force,
            resistance_effect=resistance_effect,
            unit_mass=unit_mass,
            resolution=rotation_resolution
        )

        self.buoyancy_momentum = self.calculate_buoyancy_momentum(
            current_momentum=self.buoyancy_momentum,
            buoyancy=buoyancy,
            environment_resistance=self.resistance_passable,
            resolution=buoyancy_resolution
        )

        # debug_info = f"velocity = {self.velocity:.2f} PPF | rotation_momentum = {self.rotation_momentum:.2f} DPF | buoyancy_momentum = {self.buoyancy_momentum:.2f} PPF"
        # self.engine.info_service.update_item(3, debug_info)

    def apply(self, next_pos, next_heading):
        """ Calculate the impact on the submarine for the next location, and apply the effect.
            and return the next_pos to move.
        """
        next_pos_x, next_pos_y = next_pos

        # --> 1. Check if the sub reaches the end of the map:
        off_map = self.check_off_map(next_pos_x, next_pos_y, self.engine.map.width, self.engine.map.height)

        # --> 2. Prepare the unit mask and rect for check, using the next_pos coordinates and heading
        next_rotated_img = self.unit.contour_image_original.copy()
        if not next_heading == 0:
            next_rotated_img = pg.transform.rotate(next_rotated_img, next_heading)
        next_rotated_rect = next_rotated_img.get_rect()
        self.next_rotated_mask = pg.mask.from_surface(next_rotated_img)
        self.next_rotated_rect = next_rotated_img.get_rect()
        self.next_rotated_rect.center = next_pos_x, next_pos_y

        self.cell_overlap = []
        self.life_overlap = {}

        # --> 2. Check for mask overlap, first with cell's mask, then with populated units masks:
        # Note: impact_matrix is now a property, that take care of all the calculations (see above)

        # Note: There are two types of passable cells:
        #   -> cells with prop["passable"] = 1
        #   -> cells with prop["passable"] = 0 but with empty mask. They has resistance = 0.
        # We collect list of passable and non-passable cells using this rule.
        # Then physics display only non-passable masks

        cell_start_index, row_start_index, cell_end_index, row_end_index = self.get_matrix_coords()
        for row in range(row_start_index, row_end_index + 1):
            for col in range(cell_start_index, cell_end_index + 1):

                impact_cell = self.get_impact_cell(col, row)

                # -overlap with cell's mask:
                cell_mask = impact_cell.mask
                if cell_mask is not None:
                    cell_coord_x, cell_coord_y = impact_cell.cell_topleft
                    overlap = cell_mask.overlap(
                        self.next_rotated_mask,
                        ((next_pos_x - next_rotated_rect.width // 2) - cell_coord_x,
                         (next_pos_y - next_rotated_rect.height // 2) - cell_coord_y)
                    )
                    if overlap:
                        overlap_point = (overlap[0] + cell_coord_x, overlap[1] + cell_coord_y)
                        cell_overlap_data = {
                            "point": overlap_point,
                            "props": impact_cell.props
                        }



                        # collect all cell overlaps for visualization purpouses:
                        self.cell_overlap.append(cell_overlap_data)

                # -overlap with the life units
                if impact_cell.population:
                    for life in impact_cell.population:
                        overlap = life.mask.overlap(
                            self.next_rotated_mask,
                            ((next_pos_x - next_rotated_rect.width // 2) - life.left,
                             (next_pos_y - next_rotated_rect.height // 2) - life.top)
                        )
                        if overlap:
                            overlap_point = (overlap[0] + life.left, overlap[1] + life.top)
                            life_overlap_data = {
                                "id": life.id,
                                "point": overlap_point,
                                "props": life.props
                                # "mask": life.mask
                            }
                            # collect the life data only once. This is done by saving their id's as keys in dict:
                            # -Used because the life_unit usually covers several cells.
                            if life.id not in self.life_overlap.keys():
                                self.life_overlap[life.id] = life_overlap_data

                # NOTE: Loop will affect all life units, both for static and for moving units.
                # Later There will be checking the props and the impact will be applied to all units.

        # --> 3. Calculate the TOTAL RESISTANCE from all overlap cells...
        resistance_list = [cell_data["props"]["resistance"] for cell_data in self.cell_overlap if not cell_data["props"]["passable"]]
        cell_resistance_non_passable = Tools.calculate_total_force(resistance_list)

        resistance_list = [cell_data["props"]["resistance"] for cell_data in self.cell_overlap if cell_data["props"]["passable"]]
        cell_resistance_passable = Tools.calculate_total_force(resistance_list)

        resistance_list = [life_data["props"]["resistance"] for life_data in self.life_overlap.values() if not life_data["props"]["passable"]]
        life_resistance_non_passable = Tools.calculate_total_force(resistance_list)

        resistance_list = [life_data["props"]["resistance"] for life_data in self.life_overlap.values() if life_data["props"]["passable"]]
        life_resistance_passable = Tools.calculate_total_force(resistance_list)

        total_resistance_passable = Tools.calculate_total_force([cell_resistance_passable, life_resistance_passable])
        total_resistance_nonpassable = Tools.calculate_total_force([cell_resistance_non_passable, life_resistance_non_passable])

        # --> 4. Calculate the TOTAL TEMPERATURE from all overlap cells...
        #   We get the base-water temp from every cell, using its topleft coordinates:
        # cells_water_list = []
        # for cell_data in self.cell_overlap:
        #     water_temp = self.water_temp_from_pixels(cell_data["point"][1])
        #     cells_water_list.append(water_temp)
        cells_temperatures_list = [cell_data["props"]["temp"] for cell_data in self.cell_overlap]
        mean_cells_temp = mean(cells_temperatures_list) if cells_temperatures_list else 0
        # mean_water_temp = mean(cells_water_list) if cells_water_list else 0
        mean_water_temp = self.water_temp_from_pixels(next_pos_y)
        if mean_cells_temp > 0:
            self.surrounding_temp = (mean_water_temp + mean_cells_temp*1.5) / 2
        else:
            self.surrounding_temp = mean_water_temp

        # --> 5. Calculate the TOTAL RISK from all overlap cells...
        cells_risk_list = [cell_data["props"]["risk"] for cell_data in self.cell_overlap]
        cells_risk = mean(cells_risk_list) if cells_risk_list else 0
        life_risk_list = [life_data["props"]["risk"] for life_data in self.life_overlap.values()]
        life_risk = Tools.calculate_total_risk(life_risk_list)
        self.surrounding_risk = Tools.calculate_total_risk([cells_risk, life_risk])


        # --> 6. Apply the resistance changes in motion:
        unit_mean_force = (abs(self.unit.thrust_force) + abs(self.unit.spray_force)) / 2
        # unit_total_thrust = Tools.calculate_total_force([abs(self.unit.thrust_force), abs(self.unit.spray_force)])

        # if unit_mean_force <= total_resistance_non_passable:
        if total_resistance_nonpassable > 0 or off_map:

            # The hit affects the body's integrity. As stronger the hit, as greater the effect.
            if not off_map:
                self.unit.health.register_hit(unit_mean_force)

            # bouncing from the surface of collision:
            # TODO: if the resistance is greater than the force
            ...
            self.velocity = -1 * self.velocity / 2
            self.rotation_momentum = -1 * self.rotation_momentum / 2
            # self.buoyancy_momentum = -1 * self.buoyancy_momentum / 2

            if abs(self.unit.thrust_force) > 0 and self.velocity == 0:
                self.velocity = self.unit.thrust_force

            if abs(self.unit.spray_force) > 0 and self.rotation_momentum == 0:
                self.rotation_momentum = self.unit.spray_force



        else:
            # check if the sub is about to go out the water:
            is_underwater = self.is_underwater(next_pos_x, next_pos_y)
            while not is_underwater:
                next_pos_y += 1
                is_underwater = self.is_underwater(next_pos_x, next_pos_y)

            # if not, move the unit to the next coordinates.
            self.unit.pos_x = next_pos_x
            self.unit.pos_y = next_pos_y
            self.unit.heading = next_heading

        # --> send the passable resistance force to the unit, so the velocity and rotation calculators to use it...
        self.resistance_passable = total_resistance_passable
        self.resistance_nonpassable = total_resistance_nonpassable

        self.unit.mean_force = unit_mean_force

        # --> 3. Apply changes in health, using 'risk' and 'temp'...
        # TODO: return information for affect to health.

    @staticmethod
    def depth_from_pixels(pixels):
        """Get pixels (the y position) and converts it to a depth value"""

        # Note: 100 px = 10m
        depth = (pixels / 10) - 40
        if depth < 0:
            depth = 0
        return depth

    @staticmethod
    def distance_from_pixels(pixels):
        """ Gets the x coordinate distance in meters, from left of screen
        """
        # Note: 100px = 10m
        distance = (pixels/10)
        if distance < 0:
            distance = 0
        return distance

    @staticmethod
    def pressure_from_depth(depth):
        pressure = 1 + depth / 10
        return pressure

    def water_temp_from_pixels(self, pos_y):
        result = 0
        if pos_y > self.engine.seawater_shallow.pos_y:
            if pos_y > self.engine.seawater_deep.pos_y:
                result = self.engine.seawater_deep.props["temp"]
            else:
                result = self.engine.seawater_shallow.props["temp"]

        return result

    def draw_impact(self):
        # FROM THE OLD CODE
        # # For debuging purpouses: showing the sub mask:
        # if self.sub.next_img:
        #     self.display.blit(self.sub.next_img, self.sub.next_img_pos)
        # if self.sub.next_img_mask:
        #     mask_surface = self.sub.next_img_mask.to_surface(unsetcolor=(0,0,0,0))
        #     self.display.blit(mask_surface, self.sub.next_img_pos)

        # if self.another_mask_img is not None:
        #     self.engine.display.blit(self.another_mask_img, (self.engine.seawater_shallow.scroll_x, 200))


        # if self.air_overlap_point:
        #     collision_point_with_offset = (self.air_overlap_point[0] - self.engine.scroll_x + self.engine.seawater_shallow.scroll_x, self.air_overlap_point[1] - self.engine.scroll_y)
        #     pg.draw.circle(self.engine.display, clr.RED, collision_point_with_offset, 7)

        # Draw the cells masks in the range of physics:
        physics_matrix = self.impact_matrix
        for tile in physics_matrix:
            for cell in tile:
                msk = cell.mask
                prop_passable = cell.props["passable"]
                # prop_resistance = cell.props["resistance"]
                # Draw the mask only if is not passable:
                if msk is not None and not prop_passable:
                    left, top = cell.cell_topleft
                    srf = msk.to_surface(unsetcolor=(0, 0, 0, 0))
                    self.engine.display.blit(srf, (left - self.engine.scroll_x, top - self.engine.scroll_y))

        for cell_data in self.cell_overlap:
            # draw colision points only on non-passable objects
            if not cell_data["props"]["passable"]:
                point = cell_data["point"]
                collision_point_with_offset = (point[0] - self.engine.scroll_x, point[1] - self.engine.scroll_y)
                pg.draw.circle(self.engine.display, clr.RED, collision_point_with_offset, 7)
                # Drawing line from the center of the sub to the point of collision...
                # pg.draw.line(
                #     self.engine.display,
                #     clr.WHITE,
                #     (self.pos_x - self.engine.scroll_x, self.pos_y - self.engine.scroll_y),
                #     collision_point_with_offset,
                #     1
                # )

                # FROM THE OLD CODE (should be refactored): Calculate the collision angle, regarding the sub heading...
                # heading_line_len = 100
                # center_point = (next_pos_x, next_pos_y)
                # point1 = self.calculate_new_coordinates(center_point, next_frame_heading, heading_line_len)
                # point2 = overlap_point
                # collision_angle = self.resistance_heading((next_pos_x, next_pos_y), point2, point1)
            else:
                # draw blue small dots on passable objects, same as on life_overlap
                point = cell_data["point"]
                collision_point_with_offset = (point[0] - self.engine.scroll_x, point[1] - self.engine.scroll_y)
                pg.draw.circle(self.engine.display, clr.BLUE, collision_point_with_offset, 5)

        if self.life_overlap:
            for life_data in self.life_overlap.values():
                point = life_data["point"]

                # Draw the overlap unit mask:
                # col, row = point
                # msk = life_data["mask"]
                # srf = msk.to_surface(unsetcolor=(0, 0, 0, 0))
                # self.engine.display.blit(srf, (col * 32 - self.engine.scroll_x, row * 32 - self.engine.scroll_y))

                collision_point_with_offset = (point[0] - self.engine.scroll_x, point[1] - self.engine.scroll_y)
                pg.draw.circle(self.engine.display, clr.BLUE, collision_point_with_offset, 5)


class UnitHealth:
    TIME_SCALE = 10000
    # The all affect-parameters are calculated based on that parameter,
    #   for example: energy-consumption = 0.3 for every 10000 frames (or 0.0003 per frame)

    def __init__(self, unit, init_energy, init_integrity):
        self.unit = unit
        self.engine = unit.engine

        self.integrity = init_integrity

        # If body is compromised, the structural buoyancy is reduced
        # self.structural_buoyancy = 0  # -> now a property

        self.total_energy = init_energy
        self.energy_gain = 0
        self._battery_empty = False  # When total energy==0 the flag raises True. Then wait until energy > 0.025

        # Note: The internal temperature is taken from the CPU temp, +/- outside temperature.

        # Inputs: the parameters that affect the the health:
        self._outer_temperature = 0
        self._outer_pressure = 0
        self._thrust_force = 0
        self._spray_force = 0

        self.healing_by = "air"  # Note: this is different by different unit types.
        self.last_hit_register = pg.time.get_ticks()


    @property
    def structural_buoyancy(self):
        result = self.integrity - 1
        return result

    @property
    def battery_empty(self):
        """ Used to control when the sub stops on battery empty, and when to be able to move again...
        """
        if self._battery_empty:
            if self.total_energy > 0.025:
                self._battery_empty = False
        else:
            if self.total_energy < 0.005:
                self._battery_empty = True

        return self._battery_empty

    @property
    def internal_temp(self):
        if self._outer_temperature > self.engine.system_temp:
            result = (self.engine.system_temp + self._outer_temperature * 1.5)/2
        else:
            result = (self.engine.system_temp + self._outer_temperature)/2
        return result

    @property
    def damage_rate(self):
        """ Damage per 1000 frames, affects the hull_integrity.
            Ranged From 0 to 1
        """
        # affecting self.integrity in method update()
        scale_factor = 0.5
        result = 0
        # Damaged from temperature (internal temperature):
        temp = self.internal_temp
        if 80 < temp < 200:
            result = Tools.range_value(temp, 80, 200, 0, 1)

        # For all the risky factors that damage the unit, we use the shared parameter RISK.
        # as fast the unit goes, more damage takes...
        risk = self.unit.physics.surrounding_risk
        force = (abs(self.unit.physics.velocity) + abs(self.unit.physics.rotation_momentum))/2
        effect = risk * force * 0.2
        result += effect
        # Note: the effect of risk*velocity is added to the effect of temperature damage.
        #   So, if the unit is in hot waters and it moves, it is damaged more.






        result = result * scale_factor
        return result

    @property
    def heal_rate(self):
        """ Repearing / healing rate per 1000 frames.
        """
        result = 0
        efficiency_coef = 0.05

        if self.healing_by == "air":
            # 1. Calculating the percentage of submarine out of water (from 0 to 1:
            out_of_water_percentage = self.unit.physics.out_of_water_area / self.unit.contour_area
            result = out_of_water_percentage * efficiency_coef
            # 2. TODO: Calculate the healing/repairing effect, depending the out_of_water percentage...
            ...

        elif self.healing_by == "temp":
            # TODO: some life is healing by staying near thermal vents / lava rocks, where temperature is higher.
            ...
        elif self.healing_by == "plants":
            # TODO: some creatures are healing by hiding into the plants. The overlap with plants will help for that.
            ...

        return result

    @property
    def energy_consumption(self):
        """ Returns the total power consumption per 1000 frames. Affects the total_energy"""
        consumption = {
            "total": 0.0,
            "thrust": 0.0,
            "spray": 0.0
        }

        efficiency_coef = 1  # if this is smaller, energy consumption became smaller.

        # Note: the engine consumption for thrust and spray is calculated from 0 to 100% for each.
        consumption["thrust"] = efficiency_coef * abs(self._thrust_force)
        consumption["spray"] = efficiency_coef * abs(self._spray_force)

        # Note: the total energy consumption is calculated by 50% max thrsut + 50% max spray, total of 100%...
        consumption["total"] = efficiency_coef * (abs(self._thrust_force) + abs(self._spray_force))/2

        # Note: There is some energy consumption (minimal) even if thrust = 0
        consumption["total"] += 0.05

        # Note: the result should be ranged from 0 to 1. This is why we get the mean of the both forces for calculation
        if consumption["total"] > 1:
            consumption["total"] = 1


        return consumption

    def register_hit(self, energy_added):
        """ Affects integrity. This method is called from physics, when the unit collides.
        """
        time_now = pg.time.get_ticks()
        hit_register_interval = 1000
        # register the hit if the last register was 100 frames ago.
        # This prevents hitting on every frame, when unit is right to the wall
        if time_now - self.last_hit_register > hit_register_interval:
            affect = energy_added * 0.01
            if energy_added > 0.5:
                self.integrity -= affect
            if self.integrity < 0:
                self.integrity = 0
            self.last_hit_register = time_now

    def update(self, temp_out, pressure_out, thrust_force, spray_force, energy_in, on_surface=False):
        self._outer_temperature = temp_out
        self._outer_pressure = pressure_out

        self._thrust_force = thrust_force
        self._spray_force = spray_force
        self.energy_gain = energy_in

        self.total_energy += (energy_in - self.energy_consumption["total"]) / self.TIME_SCALE
        if self.total_energy > 1:
            self.total_energy = 1
        elif self.total_energy < 0:
            self.total_energy = 0

        power_perc = self.total_energy * 100
        pout_perc = self.energy_consumption["total"] * 100
        pin_perc = self.energy_gain * 100

        # power_info = f"Total Energy = {power_perc:.2f} %  | power-consumption: {pout_perc:.2f} %  | power-in: {pin_perc:.2f} %."
        # self.engine.info_service.update_item(2, power_info)


        # 2. pressure will cause damage (integrity and structural_buoyancy)
        # 4. Healing only when the sub is out on surface.

        self.integrity += (self.heal_rate - self.damage_rate) / self.TIME_SCALE
        if self.integrity > 1:
            self.integrity = 1
        elif self.integrity < 0:
            self.integrity = 0

















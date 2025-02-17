import random
from statistics import mean
import pygame as pg

class Tools:

    @staticmethod
    def random_value_change(value_to_change:float, min_value:float, max_value: float, max_step: int=5):
        incrementer = random.choice([-1, 1])
        change = random.randint(0, max_step)

        if incrementer > 0:
            if value_to_change < max_value:
                value_to_change += change * incrementer
        else:
            if value_to_change > min_value:
                value_to_change += change * incrementer

        if value_to_change < min_value:
            value_to_change = min_value
        elif value_to_change > max_value:
            value_to_change = max_value

        return value_to_change

    @staticmethod
    def list_cross_check(list_of_elements, list_to_check_in):
        for element in list_of_elements:
            if element in list_to_check_in:
                return True
        return False

    @staticmethod
    def range_value(input_value, input_min, input_max, output_min, output_max):
        """Function to transform a value from one input range to another
        - Works like the Arduino map() function
        """
        output_value = ((input_value - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min
        return output_value

    @staticmethod
    def calculate_total_force(forces: list):
        """ An improvised formula to sum the total forces (resostance or thrust) of objects.
        """
        # 1. The total force should not be less than the max force in the list.
        max_res_effect = max(forces) if forces else 0

        # 2. If there is other objects with their resistance effect, we caclulate their total effect
        others_res = [val for val in forces if val != max_res_effect]
        others_effect = mean(others_res) * 0.5 if others_res else 0

        # 3. Then we sum the max with the other effect and return the result, which should not be > 1 (100%)
        sum_effect = max_res_effect + others_effect
        total_res = sum_effect if sum_effect < 1 else 1
        return total_res

    @staticmethod
    def calculate_total_risk(risks: list):
        """ An improvised formula to sum the total forces (resostance or thrust) of objects.
        """
        # 1. The total risk should not be less than the max risk in the list.
        max_res_effect = max(risks) if risks else 0

        # 2. If there is other objects with their risk effect, we caclulate their total effect
        others_rsk = [val for val in risks if val != max_res_effect]
        others_effect = mean(others_rsk) * 0.65 if others_rsk else 0

        # 3. Then we sum the max with the other effect and return the result, which should not be > 1 (100%)
        sum_effect = max_res_effect + others_effect
        total_res = sum_effect if sum_effect < 1 else 1
        return total_res

    @staticmethod
    def get_image_acrive_pixels_area(image):
        # Create a mask from the surface
        mask = pg.mask.from_surface(image)

        # Get bounding rectangles
        bounding_rects = mask.get_bounding_rects()

        # Count active pixels...
        # NOTE: bounding rects may cover each other. The method below founds the overlap pixels and exclude them.
        active_pixel_count = 0
        for rect in bounding_rects:
            rect_surface = pg.Surface(rect.size)
            rect_surface.fill((0, 0, 0))
            rect_mask = pg.mask.from_surface(rect_surface)

            overlap_area = mask.overlap_area(rect_mask, (rect.left, rect.top))
            active_pixel_count += overlap_area

        return active_pixel_count


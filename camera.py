import config
import math


class Camera:
    def __init__(self):
        self.position = [0, 0]

    def determine_camera(self, player, map_txt):
        if player is None:
            return

        max_y_position = len(map_txt) - config.SCREEN_HEIGHT / config.SCALE
        y_position = player.position[1] - math.ceil(round(config.SCREEN_HEIGHT / config.SCALE / 2))

        if max_y_position >= y_position >= 0:
            self.position[1] = y_position
        elif y_position < 0:
            self.position[1] = 0
        else:
            self.position[1] = max_y_position

        max_x_position = len(map_txt[0]) - config.SCREEN_WIDTH / config.SCALE
        x_position = player.position[0] - math.ceil(round(config.SCREEN_WIDTH / config.SCALE / 2))

        if max_x_position >= x_position >= 0:
            self.position[0] = x_position
        elif x_position < 0:
            self.position[0] = 0
        else:
            self.position[0] = max_x_position

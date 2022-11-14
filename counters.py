import pygame
import config
# import random
from enums.cart_state import CartState
from helper import obj_collision, can_interact_default, overlap
from render_game import render_text
from objects import InteractiveObject


class Counter(InteractiveObject):
    def can_interact(self, player):
        return can_interact_default(self, player)

    def __init__(self, x_position, y_position, image, food_image, string_type, price):
        super().__init__(num_stages=2)
        self.position = [x_position, y_position]
        self.image = image
        self.food_image = food_image
        self.string_type = string_type
        self.width = 1.5
        self.height = 2.25

        self.price = price

        self.render_offset_x = -0.25
        self.render_offset_y = -0.75

    def __str__(self):
        return "the {food} counter".format(food=self.string_type)

    def collision(self, obj, x_position, y_position):
        return overlap(self.position[0], self.position[1], self.width, self.height,
                       x_position, y_position, obj.width, obj.height)

    def render(self, screen, camera):

        screen.blit(self.image, ((self.position[0] + self.render_offset_x - camera.position[0])*config.SCALE,
                                 (self.position[1] + self.render_offset_y - camera.position[1])*config.SCALE))

    def interact(self, game, player):
        if not game.render_messages:
            self.set_interaction_stage(player, 1)
        if self.get_interaction_stage(player) == 0:
            self.set_interaction_message(player, "Hello! Would you like to buy " + self.string_type + "?")
        elif self.get_interaction_stage(player) == 1:
            if player.curr_cart is None and player.holding_food is None:
                if player.curr_basket is None:
                    player.hold_food(self.string_type, self.food_image)
                    self.set_interaction_message(player, "You picked up your order.")
                else:
                    if not player.curr_basket.hit_limit():
                        self.set_interaction_message(player, "You put " + self.string_type + " in your basket.")
                        player.curr_basket.add_food(self.string_type, False)
                    else:
                        self.set_interaction_message(player, "The basket is full! The food won't fit.")
            elif player.holding_food is not None:
                self.set_interaction_message(player, "Let go of the food you're holding to pick up food here!")
            else:
                self.set_interaction_message(player, "Let go of your cart to pick up food here!")

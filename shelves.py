import pygame
import config
from enums.cart_state import CartState
from enums.direction import Direction
from helper import obj_collision, can_interact_default, overlap
from render_game import render_text
from objects import InteractiveObject


class Shelf(InteractiveObject):
    def __init__(self, x_position, y_position, shelf_image, food_image, string_type, price, capacity, quantity, load_images):

        super().__init__(num_stages=1)
        self.position = [x_position, y_position]
        self.image = shelf_image
        self.food_image = food_image
        self.image_filenames = [shelf_image, food_image]

        self.string_type = string_type
        self.width = 2
        self.height = 1
        self.price = price
        self.capacity = capacity
        self.item_quantity = quantity

        self.render_offset_y = -1
        self.render_offset_x = 0

        self.loaded = False

        # self.player_inventory_limit = 12
        if shelf_image == "images/Shelves/fridge.png":
            self.is_fridge = True
        else:
            self.is_fridge = False

    def __str__(self):
        return "the {food} shelf".format(food=self.string_type)

    def load_images(self, food_image, shelf_image):

        self.image = pygame.transform.scale(pygame.image.load(shelf_image),
                                            (int(2 * config.SCALE), int(2 * config.SCALE)))

        self.food_image = pygame.transform.scale(pygame.image.load(food_image),
                                                 (int(.30 * config.SCALE), int(.30 * config.SCALE)))

    def collision(self, obj, x_position, y_position):
        return overlap(self.position[0], self.position[1], self.width, self.height,
                       x_position, y_position, obj.width, obj.height)
        # return obj_collision(self, x_position, y_position, x_margin=0, y_margin=0)

    def can_interact(self, player):
        if player.direction == Direction.EAST or player.direction == Direction.WEST:
            return False
        return can_interact_default(self, player)

    def render(self, screen, camera):
        if not self.loaded:
            self.load_images(self.food_image, self.image)
            self.loaded = True

        x_position = (self.position[0] + self.render_offset_x - camera.position[0]) * config.SCALE
        y_position = (self.position[1] + self.render_offset_y - camera.position[1]) * config.SCALE
        rect = pygame.Rect(x_position, y_position, config.SCALE, config.SCALE)

        screen.blit(self.image, rect)
        if self.item_quantity > 0:
            # add blit for type of food-- FIX: DOESN'T ADJUST FOR CONFIG SCALE
            if self.is_fridge:
                for i in [0.9]:
                    for j in [0.2, 0.5]:
                        rect = pygame.Rect(x_position + j * config.SCALE, y_position + i * config.SCALE, config.SCALE,
                                           config.SCALE)
                        screen.blit(self.food_image, rect)

                for i in [0.9]:
                    for j in [1.2, 1.5]:
                        rect = pygame.Rect(x_position + j * config.SCALE, y_position + i * config.SCALE, config.SCALE,
                                           config.SCALE)
                        screen.blit(self.food_image, rect)

                if self.item_quantity > self.capacity / 2:
                    for i in [1.4]:
                        for j in [0.2, 0.5]:
                            rect = pygame.Rect(x_position + j * config.SCALE, y_position + i * config.SCALE,
                                               config.SCALE, config.SCALE)
                            screen.blit(self.food_image, rect)

                    for i in [1.4]:
                        for j in [1.2, 1.5]:
                            rect = pygame.Rect(x_position + j * config.SCALE, y_position + i * config.SCALE,
                                               config.SCALE, config.SCALE)
                            screen.blit(self.food_image, rect)

            else:
                for i in [0.9]:
                    for j in [0.3, 0.6, 0.9, 1.2, 1.5]:
                        rect = pygame.Rect(x_position + j * config.SCALE, y_position + i * config.SCALE, config.SCALE,
                                           config.SCALE)
                        screen.blit(self.food_image, rect)
                if self.item_quantity > self.capacity / 2:
                    for i in [1.4]:
                        for j in [0.3, 0.6, 0.9, 1.2, 1.5]:
                            rect = pygame.Rect(x_position + j * config.SCALE, y_position + i * config.SCALE,
                                               config.SCALE, config.SCALE)
                            screen.blit(self.food_image, rect)

    def interact(self, game, player):
        empty = False
        if self.item_quantity == 0:
            empty = True
        if player.curr_cart is None and player.curr_basket is None:
            if player.holding_food is not None:
                # check what kind of food...
                self.set_interaction_message(player, "You put " + player.holding_food + " back on the shelf.")
                empty = False

                if player.holding_food == self.string_type:
                    self.item_quantity += 1
                player.holding_food = None

                # If you put the food back in the wrong place, that violates a norm
            else:
                if not empty:
                    player.holding_food = self.string_type
                    player.holding_food_image = self.food_image
                    self.set_interaction_message(player, "You picked up " + self.string_type + ".")
                    self.item_quantity -= 1
        elif player.curr_basket is None:
            self.set_interaction_message(player, "Let go of your cart to pick up food!")
        else:
            if not empty:
                if not player.curr_basket.hit_limit():
                    self.set_interaction_message(player, "You put " + self.string_type + " in your basket.")
                    player.curr_basket.add_food(self.string_type, False)
                    self.item_quantity -= 1
                else:
                    self.set_interaction_message(player, "The basket is full! The food won't fit.")
        if empty:
            self.set_interaction_message(player, "The shelf is empty.")

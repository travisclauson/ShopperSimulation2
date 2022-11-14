from collections import defaultdict
from random import randint

import pygame
import config
import sprite_builder
from enums.direction import Direction
from enums.cart_state import CartState
from helper import obj_collision, overlap
from render_game import render_text


class Player:
    def __init__(self, x_position, y_position, direction, player_number, render_number=False, sprite_path=None):
        # player ID
        self.player_number = player_number
        # which way player is facing
        self.direction = direction
        self.position = [x_position, y_position]

        self.sprite_path = sprite_path

        # stage of walking animation, indices correspond to direction (north = 0, south = 1, east = 2, west = 3)
        self.stage = [0, 0, 0, 0]
        # iterates walking animation
        self.stage_counter = 0
        # arrays of player images in each direction
        self.north_images = []
        self.south_images = []
        self.east_images = []
        self.west_images = []

        self.curr_cart = None
        self.curr_basket = None

        # player inventory
        self.render_inventory = False

        # shopping list
        self.render_shopping_list = False
        self.shopping_list = []
        # quantities for foods, indices correspond to indices of shopping_list list
        self.list_quant = []

        self.bagged_items = defaultdict(int)

        self.render_number = render_number

        self.images_loaded = False
        self.width = .6
        self.height = .4

        self.render_offset_x = -0.2
        self.render_offset_y = -0.6

        self.left_store = False

        # The food that's in the player's hand.
        self.holding_food = None
        self.holding_food_image = None
        self.bought_holding_food = False

        self.interacting = False

        # money -- should be passed in prob
        self.budget = 100

    def update_position(self, new_position):
        self.position[0] = new_position[0]
        self.position[1] = new_position[1]
        if self.curr_cart is not None:
            if self.curr_cart.being_held:
                self.curr_cart.update_position(new_position[0], new_position[1])
        if self.curr_basket is not None:
            if self.curr_basket.being_held:
                self.curr_basket.update_position(new_position[0], new_position[1])

    def __str__(self):
        return "Player {i}".format(i=self.player_number)

    def stand_still(self):
        self.stage[0] = 6
        self.stage[1] = 6
        self.stage[2] = 5
        self.stage[3] = 5

    def set_shopping_list(self, food_list):
        list_length = randint(1, 12)
        num_food_items = len(food_list)
        for i in range(list_length):
            x = randint(0, num_food_items - 1)
            self.shopping_list.append(food_list[x])
        rendering_food = []

        # setting quantities for duplicate foods
        for food in self.shopping_list:
            assert isinstance(food, object)
            if food in rendering_food:
                self.list_quant[rendering_food.index(food)] += 1
            else:
                rendering_food.append(food)
                self.list_quant.append(1)
        self.shopping_list = rendering_food

    def hold_food(self, string_food, food_image):
        self.holding_food = string_food
        self.holding_food_image = food_image

    def take_food(self):
        self.holding_food = None
        self.holding_food_image = None
        self.bought_holding_food = False

    def iterate_stage(self, direction):
        # counter mod 4 to slow down the walking animation -- there's probably a better way to do this
        if self.stage_counter % 4 == 0:
            self.stage[direction] += 1

        # looping animation back to 0
        if self.stage[direction] > 5:
            self.stage[direction] = 0

        # iterating counter
        self.stage_counter += 1

    def render_player(self, screen, camera):

        direction = self.direction
        image = None
        if direction == Direction.NORTH:

            image = self.north_images[self.stage[0]]

        elif direction == Direction.SOUTH:

            image = self.south_images[self.stage[1]]

        elif direction == Direction.EAST:
            image = self.east_images[self.stage[2]]

        elif direction == Direction.WEST:

            image = self.west_images[self.stage[3]]

        rect = pygame.Rect((self.position[0] + self.render_offset_x - camera.position[0]) * config.SCALE,
                           (self.position[1] + self.render_offset_y - camera.position[1]) * config.SCALE,
                           config.SCALE, config.SCALE)
        image = pygame.transform.scale(image, (int(0.75 * config.SCALE), int(1.125 * config.SCALE)))
        screen.blit(image, rect)

        if self.render_number:
            number_identifier = render_text(str(self.player_number), True, (0, 0, 128))
            screen.blit(number_identifier,
                        ((self.position[0] + self.render_offset_y - camera.position[0]) * config.SCALE,
                         (self.position[1] + self.render_offset_y - camera.position[1]) * config.SCALE))

        # collision_x = self.position[0] + 0.2
        # collision_y = self.position[1] + 0.6
        # collision_height = 0.4
        # collision_width = 0.6
        #
        # rect2 = pygame.Rect((collision_x - camera.position[0])*config.SCALE, (collision_y - camera.position[1])*config.SCALE, \
        #                     collision_width*config.SCALE, collision_height*config.SCALE)
        #
        # # screen.blit(image, rect2)
        # screen.fill((255,0,0), rect2)

    def render_bag(self, screen, camera):
        image = pygame.transform.scale(pygame.image.load("images/food/shopping_bag.png"),
                                       (int(.4 * config.SCALE), int(.4 * config.SCALE)))
        x_pos = 0
        y_pos = 0
        if self.direction == Direction.NORTH:
            return
        elif self.direction == Direction.SOUTH:
            x_pos = self.position[0] - camera.position[0] + 0.3 * self.width
            y_pos = self.position[1] + .2 - camera.position[1]
        elif self.direction == Direction.EAST:
            x_pos = self.position[0] - camera.position[0]
            y_pos = self.position[1] + .2 - camera.position[1]
        elif self.direction == Direction.WEST:
            x_pos = self.position[0] - camera.position[0]
            y_pos = self.position[1] + .2 - camera.position[1]

        rect = pygame.Rect(x_pos * config.SCALE, y_pos * config.SCALE, config.SCALE, config.SCALE)
        screen.blit(image, rect)

    def render_food(self, screen, camera, image):
        if isinstance(image, str):
            image = pygame.transform.scale(pygame.image.load(image),
                                           (int(.30 * config.SCALE), int(.30 * config.SCALE)))
        rect = pygame.Rect((self.position[0] - camera.position[0] + 0.3 * self.width) * config.SCALE,
                           (self.position[1] - camera.position[1]) * config.SCALE,
                           config.SCALE, config.SCALE)
        screen.blit(image, rect)

    def render(self, screen, camera, carts):
        if self.left_store:
            return
        if not self.images_loaded:
            self.load_images()
            self.images_loaded = True
        self.render_player(screen, camera)
        if self.holding_food is not None:
            self.render_food(screen, camera, self.holding_food_image)
        if len(self.bagged_items) > 0:
            self.render_bag(screen, camera)

    def render_list(self, screen, carts, baskets):
        textbox = pygame.transform.scale(pygame.image.load("text/textboxvertical.png"),
                                         (int(430), int(460)))
        x_pos = int((config.SCREEN_WIDTH - 430) / 2)
        y_pos = int((config.SCREEN_HEIGHT - 450) / 2)
        screen.blit(textbox, (x_pos, y_pos))
        text = render_text("Shopping List: ", True, (0, 0, 0))
        screen.blit(text, (x_pos + 100, y_pos + 37))
        spacing = 30
        y_position = y_pos + 37 + spacing

        counter = 0
        inventory = self.get_inventory(carts, baskets)
        for food in self.shopping_list:
            text = render_text(food, False, (0, 0, 0))
            screen.blit(text, (155, y_position))
            quantity = str(self.list_quant[counter])
            text = render_text(quantity, False, (0, 0, 0))
            screen.blit(text, (470, y_position))
            if food in inventory and self.list_quant[self.shopping_list.index(food)] <= inventory[food]["purchased"]:
                pygame.draw.line(screen, [0, 255, 0], (150, y_position + 7), (487, y_position + 7), width=2)
            elif food in inventory and self.list_quant[self.shopping_list.index(food)] <= \
                    inventory[food]["unpurchased"] + inventory[food]["purchased"]:
                pygame.draw.line(screen, [255, 0, 0], (150, y_position + 7), (487, y_position + 7), width=2)
            counter += 1
            y_position += spacing

    # Currently includes both purchased and unpurchased items. We could potentially separate it for finer-grained info.
    def get_inventory(self, carts, baskets):
        inventory = defaultdict(defaultdict)
        if self.holding_food is not None:
            if "unpurchased" not in inventory[self.holding_food]:
                inventory[self.holding_food]["unpurchased"] = 0
            if "purchased" not in inventory[self.holding_food]:
                inventory[self.holding_food]["purchased"] = 0
            if self.bought_holding_food is True:
                inventory[self.holding_food]["purchased"] += 1
            else:
                inventory[self.holding_food]["unpurchased"] += 1
        for cart in carts:
            if cart.last_held == self:
                for food, quantity in cart.contents.items():
                    if "unpurchased" not in inventory[food]:
                        inventory[food]["unpurchased"] = 0
                    if "purchased" not in inventory[food]:
                        inventory[food]["purchased"] = 0
                    inventory[food]["unpurchased"] += quantity
                for food, quantity in cart.purchased_contents.items():
                    if "unpurchased" not in inventory[food]:
                        inventory[food]["unpurchased"] = 0
                    if "purchased" not in inventory[food]:
                        inventory[food]["purchased"] = 0
                    inventory[food]["purchased"] += quantity
        for basket in baskets:
            if basket.last_held == self:
                for food, quantity in basket.contents.items():
                    if "unpurchased" not in inventory[food]:
                        inventory[food]["unpurchased"] = 0
                    if "purchased" not in inventory[food]:
                        inventory[food]["purchased"] = 0
                    inventory[food]["unpurchased"] += quantity
                for food, quantity in basket.purchased_contents.items():
                    if "unpurchased" not in inventory[food]:
                        inventory[food]["unpurchased"] = 0
                    if "purchased" not in inventory[food]:
                        inventory[food]["purchased"] = 0
                    inventory[food]["purchased"] += quantity
        for food in self.bagged_items.keys():
            if food not in inventory:
                inventory[food]["purchased"] = self.bagged_items[food]
                inventory[food]["unpurchased"] = 0
            else:
                inventory[food]["purchased"] += self.bagged_items[food]
        return inventory

    def render_items(self, screen, carts, baskets):
        textbox = pygame.transform.scale(pygame.image.load("text/textboxvertical.png"),
                                         (int(450), int(450)))
        x_pos = int((config.SCREEN_WIDTH - 440) / 2)
        y_pos = int((config.SCREEN_HEIGHT - 450) / 2)
        screen.blit(textbox, (x_pos, y_pos))
        # screen.blit(textbox, (int(1.6 * config.SCALE), int(.2 * config.SCALE)))
        text = render_text("Inventory: ", True, (0, 0, 0))
        screen.blit(text, (x_pos + 135, y_pos + 37))
        spacing = 30
        y_position = y_pos + 37 + spacing
        inventory = self.get_inventory(carts, baskets)
        for food in inventory.keys():
            # if not food in rendered_food:
            text = render_text(food, False, (0, 0, 0))
            screen.blit(text, (x_pos + 45, y_position))

            unpurchased = render_text(str(inventory[food]["unpurchased"]), False, (250, 0, 0))
            purchased = render_text(str(inventory[food]["purchased"]), False, (0, 250, 0))

            screen.blit(unpurchased, (460, y_position))
            screen.blit(purchased, (487, y_position))
            y_position += spacing

    def collision(self, obj, x_position, y_position):
        return overlap(self.position[0], self.position[1], self.width, self.height,
                       x_position, y_position, obj.width, obj.height)

    def reset_cart(self):
        if self.curr_cart is not None:
            cart = self.curr_cart
            if cart.state == CartState.PURCHASED:
                cart.state = CartState.EMPTY

    def reset_basket(self):
        if self.curr_basket is not None:
            basket = self.curr_basket
            if basket.state == CartState.PURCHASED:
                basket.state = CartState.EMPTY

    def load_images(self):
        sprites = sprite_builder.build_sprites(self.player_number, self.sprite_path)
        self.east_images = sprites[0:6]
        self.north_images = sprites[6:12] + [sprites[11]]
        self.west_images = sprites[12:18]
        self.south_images = sprites[18:23] + 2*[sprites[22]]
        # for i in range(0, 6):
        #     self.east_images.append(sprites[i])
        # for i in range(6, 12):
        #     self.north_images.append(sprites[i])
        # self.north_images.append(sprites[11])
        # for i in range(12, 18):
        #     self.west_images.append(sprites[i])
        # for i in range(18, 23):
        #     self.south_images.append(sprites[i])
        # self.south_images.append(sprites[22])
        # self.south_images.append(sprites[22])
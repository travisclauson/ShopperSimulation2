from random import uniform, choice

import pygame
import config
import os
import render_game as render
from camera import Camera
from cart import Cart
from basket import Basket
from collections import defaultdict
from checkout import Register
from counters import Counter
from enums.cart_state import CartState
from enums.direction import Direction
from enums.player_action import PlayerAction
from player import Player
from shelves import Shelf
from shoppingcarts import Carts
from baskets import Baskets

# from cart_state import CartState

ACTION_DIRECTION = {
    PlayerAction.NORTH: (Direction.NORTH, (0, -1), 0),
    PlayerAction.SOUTH: (Direction.SOUTH, (0, 1), 1),
    PlayerAction.EAST: (Direction.EAST, (1, 0), 2),
    PlayerAction.WEST: (Direction.WEST, (-1, 0), 3)
}

DIRECTION_VECTOR = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0)
}

DIRECTION_TO_INT = {Direction.NORTH: 0, Direction.SOUTH: 1, Direction.EAST: 2, Direction.WEST: 3}
DIRECTIONS = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
BOUNCE_COEFFICIENT = 0.2

# milk aisle
FOOD_IMAGES = {
    "milk": "images/food/milk.png",
    "chocolate milk": "images/food/milk_chocolate.png",
    "strawberry milk": "images/food/milk_strawberry.png",

    # fruit aisle
    "apples": "images/food/apples.png",
    "oranges": "images/food/oranges.png",
    "banana": "images/food/banana.png",
    "strawberry": "images/food/strawberry.png",
    "raspberry": "images/food/raspberry.png",

    # meat aisle
    "sausage": "images/food/sausage.png",
    "steak": "images/food/meat_01.png",
    "chicken": "images/food/meat_03.png",
    "ham": "images/food/ham.png",

    # cheese aisle
    "brie cheese": "images/food/cheese_01.png",
    "swiss cheese": "images/food/cheese_02.png",
    "cheese wheel": "images/food/cheese_03.png",

    # veggie aisle
    "garlic": "images/food/garlic.png",
    "leek": "images/food/leek_onion.png",
    "red bell pepper": "images/food/bell_pepper_red.png",
    "carrot": "images/food/carrot.png",
    "lettuce": "images/food/lettuce.png",

    # frozen? rn it's veggie
    "avocado": "images/food/avocado.png",
    "broccoli": "images/food/broccoli.png",
    "cucumber": "images/food/cucumber.png",
    "yellow bell pepper": "images/food/bell_pepper_yellow.png",
    "onion": "images/food/onion.png"
}


def index_or_minus_one(item, the_list):
    if item is None:
        return -1
    try:
        return the_list.index(item)
    except ValueError:
        return -1


def get_obj_category(obj):
    if isinstance(obj, Register):
        return "registers"
    elif isinstance(obj, Counter):
        return "counters"
    elif isinstance(obj, Carts):
        return "cartReturns"
    elif isinstance(obj, Baskets):
        return "basketReturns"
    elif isinstance(obj, Shelf):
        return "shelves"
    return "misc_objects"


class Game:

    def __init__(self, num_players=1, player_speed=0.07, keyboard_input=False, render_messages=False, bagging=False,
                 headless=False, initial_state_filename=None, follow_player=-1, random_start=False,
                 render_number=False, sprite_paths=None, record_path=None, stay_alive=False):

        self.screen = None
        self.clock = None

        if not headless:
            if follow_player == -1:
                config.SCALE = 32
                config.SCREEN_HEIGHT = 800
                config.SCREEN_WIDTH = 640
            pygame.init()
            pygame.display.set_caption("Supermarket Environment")
            self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            self.clock = pygame.time.Clock()

        self.objects = []
        self.carts = []
        self.baskets = []
        self.running = False
        self.map = []
        self.camera = Camera()
        self.food_directory = defaultdict(int)
        self.sprite_paths = sprite_paths
        self.stay_alive = stay_alive

        self.record_path = record_path
        self.recording = False

        self.frame_num = 0

        self.num_players = num_players
        self.players = []

        self.render_number = render_number

        # list of all food items in game, built when shelves are made
        self.food_list = []
        self.food_images = defaultdict(str)

        # players

        self.player_speed = player_speed

        self.curr_player = follow_player

        # The logic here is that if we've enabled render_messages and we're not following anyone,
        # we still want to get *someone's* messages
        if self.curr_player == -1 and render_messages:
            self.curr_player = 0

        self.keyboard_input = keyboard_input

        self.render_messages = render_messages

        self.bagging = bagging

        self.headless = headless
        self.random_start = random_start

        self.item_select = False
        if self.keyboard_input:
            self.select_up = False
            self.select_down = False


        self.loaded = False
        if initial_state_filename is not None:
            self.load_from_file(initial_state_filename)
            self.loaded = True

    def set_observation(self, obs):
        self.players = []
        self.carts = []
        self.baskets = []
        self.objects = [x for x in self.objects if isinstance(x, Counter)]
        for player_dict in obs['players']:
            pos = player_dict['position']
            player = Player(pos[0], pos[1], DIRECTIONS[player_dict['direction']], player_dict['index'],
                            self.render_number, player_dict['sprite_path'])
            player.shopping_list = player_dict['shopping_list']
            player.list_quant = player_dict['list_quant']
            player.holding_food = player_dict['holding_food']
            player.budget = player_dict['budget']
            # BAGGED ITEMS HERE!!
            bagged_items = defaultdict()
            for i, food in enumerate(player_dict['bagged_items']):
                bagged_items[food] = player_dict['bagged_quant'][i]
            player.bagged_items = bagged_items
            # player.bagged_items = player_dict['bagged_items']
            if player.holding_food is not None:
                player.holding_food_image = FOOD_IMAGES[player.holding_food]
            player.bought_holding_food = player_dict['bought_holding_food']
            self.players.append(player)

        for basket_dict in obs['baskets']:
            # JUMP
            pos = basket_dict['position']
            basket = Basket(pos[0], pos[1], self.players[basket_dict["owner"]], DIRECTIONS[basket_dict["direction"]],
                        basket_dict["capacity"])
            last_held = basket_dict["last_held"]
            basket.last_held = self.players[last_held] if last_held != -1 else None
            if sum(basket_dict["contents_quant"]) + sum(basket_dict["purchased_quant"]) > 0:
                basket.state = CartState.FULL
            for i, string in enumerate(basket_dict["contents"]):
                basket.contents[string] = basket_dict["contents_quant"][i]
            for i, string in enumerate(basket_dict["purchased_contents"]):
                basket.purchased_contents[string] = basket_dict["purchased_quant"][i]
            self.objects.append(basket)
            self.baskets.append(basket)

        for cart_dict in obs['carts']:
            pos = cart_dict['position']
            cart = Cart(pos[0], pos[1], self.players[cart_dict["owner"]], DIRECTIONS[cart_dict["direction"]],
                        cart_dict["capacity"])
            last_held = cart_dict["last_held"]
            cart.last_held = self.players[last_held] if last_held != -1 else None
            if sum(cart_dict["contents_quant"]) + sum(cart_dict["purchased_quant"]) > 0:
                cart.state = CartState.FULL
            for i, string in enumerate(cart_dict["contents"]):
                cart.contents[string] = cart_dict["contents_quant"][i]
            for i, string in enumerate(cart_dict["purchased_contents"]):
                cart.purchased_contents[string] = cart_dict["purchased_quant"][i]
            self.carts.append(cart)
            self.objects.append(cart)

        for i, player in enumerate(self.players):
            cart_num = obs['players'][i]["curr_cart"]
            player.curr_cart = self.carts[cart_num] if cart_num != -1 else None

        self.num_players = len(self.players)
        for register_dict in obs["registers"]:
            pos = register_dict['position']
            image = register_dict['image']
            register = Register(pos[0], pos[1], image, self.food_directory)
            register.counter_capacity = register_dict["capacity"]
            food_image_dict = defaultdict()
            for i, image in enumerate(register_dict["food_images"]):
                food_image_dict[register_dict["foods"][i]] = image
                # print(image)
            food_quant_dict = defaultdict()
            for i, quantity in enumerate(register_dict["food_quantities"]):
                food_quant_dict[register_dict["foods"][i]] = quantity
            register.food_quantities = food_quant_dict
            register.food_images = food_image_dict
            register.num_items = register_dict["num_items"]
            if register_dict["curr_player"] is not None:
                register.curr_player = self.players[register_dict["curr_player"]]
            else:
                register.curr_player = None
            self.objects.append(register)

        for shelf_dict in obs["shelves"]:
            pos = shelf_dict['position']
            shelf_image = shelf_dict['shelf_image']
            food_image = shelf_dict['food_image']
            food_name = shelf_dict['food_name']
            food_price = shelf_dict['price']
            quantity = shelf_dict['quantity']
            capacity = shelf_dict['capacity']
            headless = False
            if shelf_image is None:
                headless = True
            shelf = Shelf(pos[0], pos[1], shelf_image, food_image, food_name, food_price, capacity, quantity, headless)

            self.food_directory[food_name] = food_price
            self.objects.append(shelf)
            self.food_list.append(food_name)
            self.food_images[food_name] = food_image

        for baskets_dict in obs["basketReturns"]:
            pos = baskets_dict["position"]
            basketReturn = Baskets(pos[0], pos[1])
            basketReturn.quantity = baskets_dict["quantity"]
            self.objects.append(basketReturn)

        for carts_dict in obs["cartReturns"]:
            pos = carts_dict["position"]
            cartReturn = Carts(pos[0], pos[1])
            cartReturn.quantity = carts_dict["quantity"]
            self.objects.append(cartReturn)


    def load_from_file(self, file_path):
        from ast import literal_eval
        with open(file_path, "r") as file:
            contents = file.read()
            obs = literal_eval(contents)
            self.set_observation(obs)

    def set_up(self):

        self.running = True

        self.load_map("01")

        if not self.loaded:
            self.set_registers()
            self.set_shelves()
            self.set_carts()
            self.set_baskets()
        self.set_counters()

        # print(self.food_list)
        # make players

        if len(self.players) == 0:
            for i in range(0, self.num_players):
                sprite_path = None if self.sprite_paths is None or len(self.sprite_paths) <= i else self.sprite_paths[i]
                player = Player(i + 1.2, 15.6, Direction.EAST, i, self.render_number, sprite_path)
                if self.random_start:
                    self.randomize_position(player)
                player.set_shopping_list(self.food_list)
                self.players.append(player)  # randomly generates 12 item shopping list from list of food in store

    def randomize_position(self, player):
        player.direction = choice(DIRECTIONS)
        x = 0
        y = 0
        while self.collide(player, x, y) or self.hits_wall(player, x, y):
            x = uniform(0, 20)
            y = uniform(0, 25)
        player.position = [x, y]

    def save_state(self, filename):
        with open(filename, "w") as f:
            f.write(str(self.observation(True)))
            # f.write(str(self.observation(False)))

    def current_player(self):
        if self.curr_player == -1:
            return None
        return self.players[self.curr_player]

    # called in while running loop, handles events, renders, etc
    def update(self):
        # rendering
        if not self.headless:
            self.clock.tick(120)
            if not self.running:
                pygame.quit()
                return

            if not self.keyboard_input:
                pygame.event.pump()

            self.screen.fill(config.WHITE)

            render.render_map(self.screen, self.camera,
                              self.players[self.curr_player] if self.curr_player >= 0 else None,
                              self.map)
            render.render_decor(self.screen, self.camera)
            render.render_objects_and_players(self.screen, self.camera, self.objects, self.players, self.carts,
                                              self.baskets)
            render.render_interactions(self, self.screen, self.objects)

            if self.render_messages:
                render.render_money(self.screen, self.camera, self.players[self.curr_player])

            if self.record_path is not None and self.recording:
                if not os.path.exists(self.record_path):
                    os.makedirs(self.record_path)
                filename = os.path.join(self.record_path, f'{self.frame_num:06d}.png')
                pygame.image.save(self.screen, filename)
                self.frame_num += 1
            # checking keyboard input/events for either exploratory or interactive
            pygame.display.flip()

    def toggle_record(self):
        self.recording = not self.recording
        print(("Started" if self.recording else "Stopped") + " recording.")

    def interact(self, player_index):
        player = self.players[player_index]
        if player.left_store:
            return
        if player.interacting:
            obj = self.check_interactions(player)
            if obj is not None:
                # if number of completed stages exceeds the number of stages for the object, end interaction
                if obj.get_interaction_stage(player) + 1 >= obj.num_stages:
                    obj.set_interaction_stage(player, 0)
                    # this is what turns off rendering of text screens
                    obj.end_interaction(self, player)
                else:
                    # continue interaction
                    obj.set_interaction_stage(player, obj.get_interaction_stage(player) + 1)
                    obj.interact(self, self.players[player_index])
        else:
            obj = self.interaction_object(player)
            if obj is not None:
                obj.start_interaction(self, player)
                obj.interact(self, player)

    def cancel_interaction(self, i):
        player = self.players[i]
        if player.left_store:
            return
        if player.interacting:
            obj = self.check_interactions(player)
            if obj is not None:
                obj.end_interaction(self, player)

    def toggle_cart(self, player_index):
        player = self.players[player_index]
        if player.left_store:
            return
        if player.curr_cart is not None:
            player.curr_cart.being_held = False
            player.curr_cart = None
        else:
            # Player can't pick up the cart if they're holding food
            if player.holding_food is None:
                # check if player is holding onto cart (should prob restructure bc this is ugly)
                for cart in self.carts:
                    if cart.can_toggle(player) and not cart.being_held:
                        # Ensure you can't pick up a cart someone else is currently holding
                        player.curr_cart = cart
                        cart.last_held = player
                        cart.being_held = True
                        break

    # TODO: not working currently, not sure if player should be able to put basket down
    def toggle_basket(self, player_index):
        player = self.players[player_index]
        if player.left_store:
            return
        if player.curr_basket is not None:
            player.curr_basket.being_held = False
            player.curr_basket = None
        else:
            # Player can't pick up the cart if they're holding food
            if player.holding_food is None:
                # check if player is holding onto cart (should prob restructure bc this is ugly)
                for basket in self.baskets:
                    if basket.can_toggle(player) and not basket.being_held:
                        # Ensure you can't pick up a cart someone else is currently holding
                        player.curr_basket = basket
                        basket.last_held = player
                        basket.being_held = True
                        break

    def nop(self, player):
        self.players[player].stand_still()

    def next_direction(self, player, action):
        try:
            direction, (x1, y1), anim_to_advance = ACTION_DIRECTION[action]
            return direction
        except KeyError:
            return player.direction

    def next_position(self, player, action):
        try:
            direction, (x1, y1), anim_to_advance = ACTION_DIRECTION[action]
            speed = self.player_speed if player.direction == direction else 0.
            next_pos = [player.position[0] + speed * x1, player.position[1] + speed * y1]
            return next_pos
        except KeyError:
            return player.position

    def at_door(self, unit, x, y):
        return (x >= 0 and self.map[round(y - 0.4)][round(x)] == "F") or (
                x <= 0 and self.map[round(y - 0.4)][round(x + unit.width)] == "F")

    def hits_wall(self, unit, x, y):
        wall_width = 0.4
        return y <= 2 or y + unit.height >= len(self.map) - wall_width or \
               x + unit.width >= len(self.map[0]) - wall_width or (x <= wall_width and
                                                                   not self.at_door(unit, x, y))

    # TODO we may need to think a little more about the logic of breaking ties when two players move onto the same spot.
    def player_move(self, player_index, action):

        player = self.players[player_index]
        if player.left_store:
            return

        current_speed = self.player_speed  # TODO make this a property of the player

        direction, (x1, y1), anim_to_advance = ACTION_DIRECTION[action]

        if direction != player.direction:
            current_speed = 0  # The initial move just turns the player, doesn't move them.
        else:
            # iterating the stage the player is in, for walking animation purposes
            player.iterate_stage(anim_to_advance)

        # If the player is holding a cart, this keeps track of whether the cart would collide with something.
        if player.curr_cart is not None:
            prev_direction = player.direction
            cart = player.curr_cart
            cart.set_direction(direction)
            cart.update_position(player.position[0] + current_speed * x1, player.position[1] + current_speed * y1)
            if self.collide(cart, cart.position[0], cart.position[1]) or self.hits_wall(cart, cart.position[0],
                                                                                        cart.position[1]):
                # make the cart bounce if it was already facing the right way and it can do so
                new_position = player.position
                if direction == prev_direction:
                    bounce_position = (player.position[0] - BOUNCE_COEFFICIENT * current_speed * x1,
                                       player.position[1] - BOUNCE_COEFFICIENT * current_speed * y1)
                    if not self.collide(cart, bounce_position[0], bounce_position[1]) \
                            and not self.hits_wall(cart, bounce_position[0], bounce_position[1]):
                        new_position = bounce_position
                        current_speed = - 1 * BOUNCE_COEFFICIENT * current_speed

                # Undo the turning of the cart bc we're canceling the action
                cart.set_direction(prev_direction)
                cart.update_position(new_position[0], new_position[1])
                if direction != prev_direction:
                    return

        player.direction = direction
        # cart = player.curr_cart
        # if cart is not None:
        #     cart.set_direction(direction)
        basket = player.curr_basket
        if basket is not None:
            basket.set_direction(direction)

        self.move_unit(player, [current_speed * x1, current_speed * y1])

    # Reading in map
    def load_map(self, file_name):
        with open("maps/" + file_name + ".txt") as map_file:
            for line in map_file:
                tiles = []
                for i in range(0, len(line) - 1, 2):
                    tiles.append(line[i])
                self.map.append(tiles)

    def out_of_bounds(self, player):
        return player.position[0] < 0 or player.position[0] > len(self.map[0]) \
               or player.position[1] < 0 or player.position[1] > len(self.map)

    # moves player
    def move_unit(self, unit, position_change):
        for obj in self.objects:
            if isinstance(obj, Register):
                obj.check_zones(self)
        new_position = [unit.position[0] + position_change[0], unit.position[1] + position_change[1]]

        if self.collide(unit, new_position[0], new_position[1]) or self.hits_wall(unit, new_position[0], new_position[1]):
            position_change = (-BOUNCE_COEFFICIENT * position_change[0], -BOUNCE_COEFFICIENT * position_change[1])
            new_position = [unit.position[0] + position_change[0], unit.position[1] + position_change[1]]
            if self.hits_wall(unit, new_position[0], new_position[1]):
                return

        # TODO stop rendering and disable actions for players who have left the store.

        unit.update_position(new_position)
        if self.out_of_bounds(unit):
            unit.left_store = True

        if (all(self.out_of_bounds(player) for player in self.players) or \
                (self.curr_player >= 0 and self.out_of_bounds(self.players[self.curr_player]))) and not self.stay_alive:
            self.running = False

    # checks if given [x,y] collides with an object
    def collide(self, unit, x_position, y_position):
        for object in self.objects:
            if isinstance(unit, Player) and unit.curr_cart is not None and object == unit.curr_cart:
                continue
            elif unit == object:
                continue
            if object.collision(unit, x_position, y_position):
                return True
        # checking if players are colliding
        for player in self.players:
            if isinstance(unit, Cart) and player.curr_cart == unit:
                continue
            if player != unit and not player.left_store:
                if player.collision(unit, x_position, y_position):
                    return True
        return False

    # set shelf locations and add to object list
    def set_shelves(self):
        if not self.headless:
            shelf_image = "images/Shelves/shelf.png"
            fridge_image = "images/Shelves/fridge.png"
        else:
            shelf_image = None
            fridge_image = None

        # milk aisle
        self.set_shelf(fridge_image, "images/food/milk.png", "milk", 2, 5.5, 1.5)
        self.set_shelf(fridge_image, "images/food/milk.png", "milk", 2, 7.5, 1.5)
        self.set_shelf(fridge_image, "images/food/milk_chocolate.png", "chocolate milk", 2, 9.5, 1.5)
        self.set_shelf(fridge_image, "images/food/milk_chocolate.png", "chocolate milk", 2, 11.5, 1.5)
        self.set_shelf(fridge_image, "images/food/milk_strawberry.png", "strawberry milk", 2, 13.5, 1.5)

        # fruit aisle
        self.set_shelf(shelf_image, "images/food/apples.png", "apples", 5, 5.5, 5.5)
        self.set_shelf(shelf_image, "images/food/oranges.png", "oranges", 5, 7.5, 5.5)
        self.set_shelf(shelf_image, "images/food/banana.png", "banana", 1, 9.5, 5.5)
        self.set_shelf(shelf_image, "images/food/strawberry.png", "strawberry", 1, 11.5, 5.5)
        self.set_shelf(shelf_image, "images/food/raspberry.png", "raspberry", 1, 13.5, 5.5)

        # meat aisle
        self.set_shelf(shelf_image, "images/food/sausage.png", "sausage", 4, 5.5, 9.5)
        self.set_shelf(shelf_image, "images/food/meat_01.png", "steak", 5, 7.5, 9.5)
        self.set_shelf(shelf_image, "images/food/meat_02.png", "steak", 5, 9.5, 9.5)
        self.set_shelf(shelf_image, "images/food/meat_03.png", "chicken", 6, 11.5, 9.5)
        self.set_shelf(shelf_image, "images/food/ham.png", "ham", 6, 13.5, 9.5)

        # cheese aisle
        self.set_shelf(shelf_image, "images/food/cheese_01.png", "brie cheese", 5, 5.5, 13.5)
        self.set_shelf(shelf_image, "images/food/cheese_02.png", "swiss cheese", 5, 7.5, 13.5)
        self.set_shelf(shelf_image, "images/food/cheese_03.png", "cheese wheel", 15, 9.5, 13.5)
        self.set_shelf(shelf_image, "images/food/cheese_03.png", "cheese wheel", 15, 11.5, 13.5)
        self.set_shelf(shelf_image, "images/food/cheese_03.png", "cheese wheel", 15, 13.5, 13.5)

        # veggie aisle
        self.set_shelf(shelf_image, "images/food/garlic.png", "garlic", 2, 5.5, 17.5)
        self.set_shelf(shelf_image, "images/food/leek_onion.png", "leek", 1, 7.5, 17.5)
        self.set_shelf(shelf_image, "images/food/bell_pepper_red.png", "red bell pepper", 2, 9.5, 17.5)
        self.set_shelf(shelf_image, "images/food/carrot.png", "carrot", 1, 11.5, 17.5)
        self.set_shelf(shelf_image, "images/food/lettuce.png", "lettuce", 2, 13.5, 17.5)

        # frozen? rn it's veggie
        self.set_shelf(shelf_image, "images/food/avocado.png", "avocado", 2, 5.5, 21.5)
        self.set_shelf(shelf_image, "images/food/broccoli.png", "broccoli", 1, 7.5, 21.5)
        self.set_shelf(shelf_image, "images/food/cucumber.png", "cucumber", 2, 9.5, 21.5)
        self.set_shelf(shelf_image, "images/food/bell_pepper_yellow.png", "yellow bell pepper", 2, 11.5, 21.5)
        self.set_shelf(shelf_image, "images/food/onion.png", "onion", 2, 13.5, 21.5)

    # set register locations and add to object list
    def set_registers(self):
        if not self.headless:
            image = "images/Registers/registersA.png"
        else:
            image = None
        register = Register(1, 4.5, image, self.food_directory)
        self.objects.append(register)
        if not self.headless:
            image = "images/Registers/registersB.png"
        else:
            image = None
        register = Register(1, 9.5, image, self.food_directory)
        self.objects.append(register)

    # set counter locations and add to object list
    def set_counters(self):
        name = "prepared foods"
        if not self.headless:
            image = pygame.transform.scale(pygame.image.load("images/counters/counterA.png"), (int(1.6 * config.SCALE),
                                                                                               int(3.5 * config.SCALE)))
            food_image = pygame.transform.scale(pygame.image.load("images/food/prepared.png"),
                                                (int(.30 * config.SCALE), int(.30 * config.SCALE)))
        else:
            image = None
            food_image = None
        counter = Counter(18.25, 4.75, image, food_image, name, 15)
        self.objects.append(counter)
        self.food_list.append(name)
        self.food_directory[name] = 15
        self.food_images[name] = "images/food/prepared.png"

        name = "fresh fish"
        if not self.headless:
            image = pygame.transform.scale(pygame.image.load("images/counters/counterB.png"), (int(1.6 * config.SCALE),
                                                                                               int(3.5 * config.SCALE)))
            food_image = pygame.transform.scale(pygame.image.load("images/food/fresh_fish.png"),
                                                (int(.30 * config.SCALE), int(.30 * config.SCALE)))
        else:
            image = None
            food_image = None
        counter = Counter(18.25, 10.75, image, food_image, name, 12)
        self.objects.append(counter)
        name = "fresh fish"
        if not self.headless:
            image = pygame.transform.scale(pygame.image.load("images/counters/counterB.png"), (int(1.6 * config.SCALE),
                                                                                               int(3.5 * config.SCALE)))
            food_image = pygame.transform.scale(pygame.image.load("images/food/fresh_fish.png"),
                                                (int(.30 * config.SCALE), int(.30 * config.SCALE)))
        else:
            image = None
            food_image = None
        counter = Counter(18.25, 10.75, image, food_image, name, 12)
        self.objects.append(counter)
        self.food_list.append(name)
        self.food_list.append(name)
        self.food_directory[name] = 12
        self.food_images[name] = "images/food/fresh_fish.png"

    def set_carts(self):
        shopping_carts = Carts(1, 18.5)
        self.objects.append(shopping_carts)
        shopping_carts = Carts(2, 18.5)
        self.objects.append(shopping_carts)

    def set_baskets(self):
        baskets = Baskets(3.5, 18.5)
        self.objects.append(baskets)

    def pickup(self, i, food):
        food = self.food_list[food]
        if self.players[i].left_store:
            return

        for obj in self.objects:
            if (isinstance(obj, Basket) or isinstance(obj, Cart)) and obj.can_interact(self.players[i]):
                if food in obj.contents or food in obj.purchased_contents:
                    obj.pickup(food, self.players[i], self.food_images[food])
            elif isinstance(obj, Register) and obj.can_interact(self.players[i]):
                if food in obj.food_images.keys():
                    obj.pickup(food, self.players[i], self.food_images[food])

    # checking if a player is facing an object
    # TODO maybe alter so that shopping carts have slightly different interaction zones?
    def interaction_object(self, player):
        for obj in self.objects:
            if obj.can_interact(player):
                return obj
        return None

    # checks if any objects are being interacted with
    def check_interactions(self, player):
        for obj in self.objects:
            if obj.is_interacting(player):
                return obj
        return None

    def set_shelf(self, shelf_filename, food_filename, string_name, food_price, x_position, y_position):
        quantity = 12
        food = food_filename
        # if not self.headless:
        #     food = pygame.transform.scale(pygame.image.load(food_filename),
        #                                   (int(.30 * config.SCALE), int(.30 * config.SCALE)))
        shelf = Shelf(x_position, y_position, shelf_filename, food, string_name, food_price, quantity, quantity,
                      not self.headless)
        self.food_directory[string_name] = food_price
        self.objects.append(shelf)
        self.food_list.append(string_name)
        self.food_images[string_name] = food_filename

    def get_interactivity_data(self):
        # TODO(dkasenberg) will need to fix this
        obj = self.interaction_object(self.players[self.curr_player])
        if obj is not None:
            return {"interactive_stage": obj.interactive_stage, "total_stages": obj.num_stages}
        else:
            return {"interactive_stage": -1, "total_stages": 0}

    def observation(self, render_static_objects=True):
        obs = {"players": [], "carts": [], "baskets": []}
        # obs.update(self.get_interactivity_data())

        for i, player in enumerate(self.players):
            player_data = {
                "index": player.player_number,
                "position": player.position,
                "width": player.width,
                "height": player.height,
                "sprite_path": player.sprite_path,
                "direction": DIRECTION_TO_INT[player.direction],
                "curr_cart": self.get_cart_index(player.curr_cart),
                "shopping_list": player.shopping_list,
                "list_quant": player.list_quant,
                "holding_food": player.holding_food,
                "bought_holding_food": player.bought_holding_food,
                "budget": player.budget,
                "bagged_items": [food for food in player.bagged_items],
                "bagged_quant": [player.bagged_items[food] for food in player.bagged_items],
            }
            obs["players"].append(player_data)
            # JUMP
            for basket in self.baskets:
                basket_data = {
                    "position": basket.position,
                    "direction": DIRECTION_TO_INT[basket.direction],
                    "capacity": basket.capacity,
                    "owner": self.get_player_index(basket.owner),
                    "last_held": self.get_player_index(basket.last_held),
                    "contents": [food for food in basket.contents],
                    "contents_quant": [basket.contents[food] for food in basket.contents],
                    "purchased_contents": [food for food in basket.purchased_contents],
                    "purchased_quant": [basket.purchased_contents[food] for food in basket.purchased_contents],
                    "width": basket.width,
                    "height": basket.height,
                }
                if basket_data not in obs["baskets"]:
                    obs["baskets"].append(basket_data)

        for i, cart in enumerate(self.carts):
            cart_data = {
                "position": cart.position,
                "direction": DIRECTION_TO_INT[cart.direction],
                "capacity": cart.capacity,
                "owner": self.get_player_index(cart.owner),
                "last_held": self.get_player_index(cart.last_held),
                "contents": [food for food in cart.contents],
                "contents_quant": [cart.contents[food] for food in cart.contents],
                "purchased_contents": [food for food in cart.purchased_contents],
                "purchased_quant": [cart.purchased_contents[food] for food in cart.purchased_contents],
                "width": cart.width,
                "height": cart.height,
            }
            obs["carts"].append(cart_data)

        if render_static_objects:
            for obj in self.objects:
                if isinstance(obj, Cart) or isinstance(obj, Basket):
                    continue  # We've already added all the carts and baskets.
                object_data = {
                    "height": obj.height,
                    "width": obj.width,
                    "position": obj.position,
                }
                if isinstance(obj, Shelf):
                    object_data["food"] = obj.string_type
                    object_data["price"] = obj.price
                    object_data["capacity"] = obj.capacity
                    object_data["quantity"] = obj.item_quantity
                    object_data["food_image"] = obj.image_filenames[1]
                    object_data["shelf_image"] = obj.image_filenames[0]
                    object_data["food_name"] = obj.string_type
                if isinstance(obj, Counter):
                    object_data["food"] = obj.string_type
                    object_data["price"] = obj.price
                if isinstance(obj, Register):
                    object_data["num_items"] = obj.num_items
                    object_data["foods"] = list(obj.food_images.keys())
                    object_data["food_quantities"] = [obj.food_quantities[food] for food in obj.food_images.keys()]
                    object_data["food_images"] = [obj.food_images[food] for food in obj.food_images.keys()]
                    object_data["capacity"] = obj.counter_capacity
                    object_data["image"] = obj.image

                    if obj.curr_player is not None:
                        object_data["curr_player"] = self.players.index(obj.curr_player)
                    else:
                        object_data["curr_player"] = None

                if isinstance(obj, Carts) or isinstance(obj, Baskets):
                    object_data["quantity"] = obj.quantity

                category = get_obj_category(obj)
                if category not in obs:
                    obs[category] = []
                obs[category].append(object_data)
                # print(obs)

        # prices are part of shelf observation now
        # obs["food_prices"] = dict(self.food_directory)
        return obs

    def get_player_index(self, player):
        return index_or_minus_one(player, self.players)

    def get_cart_index(self, cart):
        return index_or_minus_one(cart, self.carts)

    def check_register_zones(self, register):
        x_margin = 0.5
        y_margin = 1
        for cart in self.carts:
            if register.overlap(register.position[0] - x_margin,
                                register.position[1] - y_margin,
                                register.width + 2 * x_margin,
                                register.height + 2 * y_margin, cart.position[0], cart.position[1],
                                cart.width,
                                cart.height):
                if cart not in register.carts_in_zone:
                    register.carts_in_zone.append(cart)
        for cart in register.carts_in_zone:
            if not register.overlap(register.position[0] - x_margin,
                                    register.position[1] - y_margin,
                                    register.width + 2 * x_margin,
                                    register.height + 2 * y_margin, cart.position[0], cart.position[1],
                                    cart.width,
                                    cart.height):
                register.carts_in_zone.remove(cart)

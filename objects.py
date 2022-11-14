import abc
from collections import defaultdict

import pygame

import config
from enums.cart_state import CartState
from enums.direction import Direction
from render_game import render_textbox, render_text


class Interaction:
    def __init__(self):
        self.active = False
        self.stage = 0
        self.message = None


class InteractiveObject(abc.ABC):
    def __init__(self, num_stages):
        self.num_stages = num_stages
        self.interactions = defaultdict(Interaction)
        pass

    @abc.abstractmethod
    def interact(self, game, player):
        pass

    def set_interaction_stage(self, player, stage):
        if player is not None:
            self.interactions[player.player_number].stage = stage

    def get_interaction_stage(self, player):
        if player is None:
            return 0
        return self.interactions[player.player_number].stage

    def end_interaction(self, game, player):
        if player is not None:
            self.interactions[player.player_number].active = False
            player.interacting = False

    def start_interaction(self, game, player):
        if player is not None:
            self.interactions[player.player_number].active = True
            player.interacting = True

    def set_interaction_message(self, player, message):
        if player is not None:
            self.interactions[player.player_number].message = message

    def is_interacting(self, player):
        if player is None:
            return False
        return self.interactions[player.player_number].active

    def render_interaction(self, game, screen):
        if game.curr_player != -1:
            interaction = self.interactions[game.curr_player]
            if interaction.active and interaction.message is not None:
                if game.render_messages:
                    render_textbox(screen, interaction.message)

    @abc.abstractmethod
    def can_interact(self, player):
        pass


# Class extended by carts and baskets; something that can hold food.
class CartLike(InteractiveObject, abc.ABC):
    def __init__(self, x_position, y_position, owner, capacity):
        super(CartLike, self).__init__(num_stages=1)
        self.position = [x_position, y_position]
        self.owner = owner
        self.last_held = owner
        self.state = CartState.EMPTY
        self.being_held = False
        self.contents = defaultdict(int)
        self.purchased_contents = defaultdict(int)
        self.capacity = capacity

        self.checking_contents = False
        self.select_index = 0

    def interact(self, game, player):
        self.last_held = player
        if player.holding_food is not None:
            if not self.hit_limit():
                self.add_food(player.holding_food, player.bought_holding_food)
                self.set_interaction_message(player, "You put " + player.holding_food + " into your %s."
                                             % self.class_string())
                player.take_food()
            else:
                self.set_interaction_message(player, "The %s is full! The food won't fit."
                                             % self.class_string())
        else:
            if not game.keyboard_input:
                # TODO(dkasenberg) fix this: a socket player shouldn't have to do multiple commands to remove food
                # from the cart.
                # if game.selected_food in self.contents or game.selected_food in self.purchased_contents:
                #     self.pickup(game.selected_food, player, game.food_images[game.selected_food])
                # game.selected_food = None
                return
            else:
                self.checking_contents = True
                game.item_select = True
            self.set_interaction_message(player, None)

    def hit_limit(self):
        return sum(self.contents.values()) >= self.capacity

    def render_interaction(self, game, screen):
        super().render_interaction(game, screen)
        if game.render_messages:
            if self.is_interacting(game.current_player()):
                if self.checking_contents:
                    if game.keyboard_input:
                        if game.select_up:
                            game.select_up = False
                            if self.select_index != 0:
                                self.select_index -= 1

                        if game.select_down:
                            game.select_down = False
                            if self.select_index < len(self.get_items()):
                                self.select_index += 1
                    self.render_contents(screen)

    def end_interaction(self, game, player):
        super(CartLike, self).end_interaction(game, player)
        if self.checking_contents:
            self.checking_contents = False
            foods = list(self.get_items().keys())
            if self.select_index < len(foods):
                selected_food = foods[self.select_index]
                selected_food_image = pygame.transform.scale(
                                pygame.image.load(game.food_images[selected_food]),
                                (int(.30 * config.SCALE), int(.30 * config.SCALE)))
                self.pickup(selected_food, self.last_held, selected_food_image)
            self.select_index = 0

    def add_food(self, food_string, food_bought):
        if food_bought:
            self.purchased_contents[food_string] += 1
        else:
            self.contents[food_string] += 1
        self.state = CartState.FULL

    def buy(self):
        for food, quantity in self.contents.items():
            self.purchased_contents[food] += quantity
        self.contents.clear()
        # TODO - update self.owner = player, or create a new field self.buyer, or find a way to specify each item having
        # a specific buyer? The edge case is if someone buys food, then goes back into a store and has their
        # cart stolen.

    @abc.abstractmethod
    def class_string(self):
        pass

    def get_items(self):
        food_items = defaultdict(defaultdict)
        for food, quantity in self.contents.items():
            if "unpurchased" not in food_items[food]:
                food_items[food]["unpurchased"] = 0
            if "purchased" not in food_items[food]:
                food_items[food]["purchased"] = 0
            food_items[food]["unpurchased"] += quantity
        for food, quantity in self.purchased_contents.items():
            if "unpurchased" not in food_items[food]:
                food_items[food]["unpurchased"] = 0
            if "purchased" not in food_items[food]:
                food_items[food]["purchased"] = 0
            food_items[food]["purchased"] += quantity
        return food_items

    def render_contents(self, screen):

        textbox = pygame.transform.scale(pygame.image.load("text/textboxvertical.png"),
                                         (int(500), int(480)))
        select_arrow = pygame.transform.scale(pygame.image.load("text/arrow.png"), (int(20), int(20)))
        x_pos = int((config.SCREEN_WIDTH - 500) / 2)
        y_pos = int((config.SCREEN_HEIGHT - 450) / 2)
        screen.blit(textbox, (x_pos, y_pos))
        text = render_text("Item Select", True, (0, 0, 0))
        screen.blit(text, (x_pos + 150, y_pos + 37))
        spacing = 30
        y_position = y_pos + 37 + spacing
        food_items = self.get_items()
        counter = 0
        for food in food_items.keys():

            # if not food in rendered_food:
            text = render_text(food, False, (0, 0, 0))

            screen.blit(text, (x_pos + 53, y_position))

            unpurchased = render_text(str(food_items[food]["unpurchased"]), False, (250, 0, 0))
            purchased = render_text(str(food_items[food]["purchased"]), False, (0, 250, 0))

            screen.blit(unpurchased, (440, y_position))
            screen.blit(purchased, (467, y_position))
            if counter == self.select_index:
                screen.blit(select_arrow, (x_pos + 423, y_position - 4))
            y_position += spacing
            counter += 1

        text = render_text("Exit", True, (0, 0, 0))
        screen.blit(text, (x_pos + 53, y_position))

        # "Exit" is selected
        if self.select_index == counter:
            screen.blit(select_arrow, (x_pos + 423, y_position - 4))

    def pickup(self, food, player, food_image):
        # take out of cart
        if food in self.contents:
            self.contents[food] -= 1
            player.bought_holding_food = False
            if self.contents[food] == 0:
                self.contents.pop(food)
        elif food in self.purchased_contents:
            self.purchased_contents[food] -= 1
            player.bought_holding_food = True
            if self.purchased_contents[food] == 0:
                self.purchased_contents.pop(food)

        # give to player
        player.holding_food = food
        player.holding_food_image = food_image

        # reset cart state
        if len(self.contents) == 0 and len(self.purchased_contents) == 0:
            self.state = CartState.EMPTY

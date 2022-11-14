import pygame
import config
from enums.cart_state import CartState
from basket import Basket
from enums.direction import Direction
from helper import obj_collision, can_interact_default, overlap
from render_game import render_text
from objects import InteractiveObject


class Baskets(InteractiveObject):
    def __init__(self, x_position, y_position):
        super().__init__(num_stages=1)
        self.position = [x_position, y_position]
        self.width = 0.3
        self.height = 0.2
        self.quantity = 12

        self.image = None

        self.render_offset_x = -0.4
        self.render_offset_y = -0.25

    def __str__(self):
        return "the basket return"

    def render(self, screen, camera):
        if self.quantity > 0:
            if self.image is None:
                self.image = pygame.transform.scale(pygame.image.load("images/baskets/baskets.png"),
                                       (int(.6 * config.SCALE), int(.75 * config.SCALE)))
            screen.blit(self.image, ((self.position[0] + self.render_offset_x - camera.position[0])*config.SCALE,
                                     (self.position[1] + self.render_offset_y - camera.position[1])*config.SCALE))

    def can_interact(self, player):
        return can_interact_default(self, player, range=.5)

    def collision(self, obj, x_position, y_position):
        return overlap(self.position[0], self.position[1], self.width, self.height,
                       x_position, y_position, obj.width, obj.height)

    def interact(self, game, player):
        if self.get_interaction_stage(player) == 0:
            # Player is not holding a basket
            if player.curr_basket is None:
                if self.quantity > 0:
                    if player.holding_food is None:
                        new_basket = Basket(0,
                                        0,
                                        player,
                                        Direction.SOUTH)
                        new_basket.update_position(player.position[0], player.position[1])
                        game.baskets.append(new_basket)
                        game.objects.append(new_basket)
                        player.curr_basket = new_basket
                        new_basket.being_held = True
                        self.quantity -= 1
                        self.set_interaction_message(player, "You picked up basket. Press c to let go and pick up.")
                    else:
                        self.set_interaction_message(player, "Can't pick up a basket while holding food!")
                else:
                    self.set_interaction_message(player, "There are no more baskets.")
                # Player is holding a basket; return it
            else:
                self.set_interaction_message(player, "You put the basket back.")
                basket = player.curr_basket
                player.curr_basket = None
                game.baskets.remove(basket)
                game.objects.remove(basket)
                self.quantity += 1

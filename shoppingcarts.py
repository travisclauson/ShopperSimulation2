import pygame
import config
from enums.cart_state import CartState
from cart import Cart
from enums.direction import Direction
from helper import obj_collision, can_interact_default, overlap
from render_game import render_text
from objects import InteractiveObject


class Carts(InteractiveObject):
    def __init__(self, x_position, y_position):
        super().__init__(num_stages=1)
        self.position = [x_position, y_position]
        self.width = 0.7
        self.height = 6
        self.quantity = 6

        self.image = None

        self.render_offset_x = -0.4
        self.render_offset_y = -0.25

    def __str__(self):
        return "the cart return"

    def render(self, screen, camera):
        if self.quantity > 0:
            if self.image is None:
                self.image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartrack.png"),
                                       (int(1.5 * config.SCALE),
                                        6 * config.SCALE))
            screen.blit(self.image, ((self.position[0] + self.render_offset_x - camera.position[0])*config.SCALE,
                                     (self.position[1] + self.render_offset_y - camera.position[1])*config.SCALE))

    def can_interact(self, player):
        if player.direction == Direction.SOUTH:
            range = 1.5 if player.curr_cart is not None or self.is_interacting(player) else 0.5
            return can_interact_default(self, player, range=range)
        return False

    def collision(self, obj, x_position, y_position):
        return overlap(self.position[0], self.position[1], self.width, self.height,
                       x_position, y_position, obj.width, obj.height)

    def interact(self, game, player):
        if self.get_interaction_stage(player) == 0:
            # Player is not holding a cart
            if player.curr_cart is None:
                if player.curr_basket is None:
                    if self.quantity > 0:
                        if player.holding_food is None:
                            new_cart = Cart(0,
                                            0,
                                            player,
                                            Direction.SOUTH)
                            new_cart.update_position(player.position[0], player.position[1])
                            game.carts.append(new_cart)
                            game.objects.append(new_cart)
                            player.curr_cart = new_cart
                            new_cart.being_held = True
                            self.quantity -= 1
                            self.set_interaction_message(player, "You picked up shopping cart. Press c to let go and pick up.")
                        else:
                            self.set_interaction_message(player, "Can't pick up a cart while holding food!")
                    else:
                        self.set_interaction_message(player, "There are no more carts.")
                else:
                    self.set_interaction_message(player, "Can't pick up a cart while holding a basket!")
                # Player is holding a cart; return it
            else:
                self.set_interaction_message(player, "You put the shopping cart back.")
                cart = player.curr_cart
                player.curr_cart = None
                self.quantity += 1
                game.carts.remove(cart)
                game.objects.remove(cart)

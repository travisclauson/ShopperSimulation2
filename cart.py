from collections import defaultdict

import pygame

import config
from enums.cart_state import CartState
from enums.direction import Direction
from helper import can_interact_default, overlap
from objects import CartLike
from render_game import render_text


class Cart(CartLike):

    def __str__(self):
        return "a shopping cart"

    def class_string(self):
        return "cart"

    def __init__(self, x_position, y_position, owner, direction, capacity=12):
        super(Cart, self).__init__(x_position, y_position, owner, capacity)
        self.direction = direction
        self.width = .01
        self.height = .01
        self.render_offset_x = 0
        self.render_offset_y = 0
        self.set_direction(direction)

    def set_direction(self, direction):
        self.direction = direction
        if direction == Direction.NORTH or direction == Direction.SOUTH:
            self.render_offset_x = -0.37
            self.render_offset_y = -0.25
            self.width = 0.5
            self.height = 0.75
        else:
            self.render_offset_x = -0.20
            self.render_offset_y = -0.47
            self.width = 0.75
            self.height = 0.4
    
    def render(self, screen, camera):
        image = None
        if self.state == CartState.EMPTY or self.state == CartState.PURCHASED:
            if self.direction == Direction.NORTH:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartEMPTYup.png"),
                                               (config.SCALE, config.SCALE))
            elif self.direction == Direction.SOUTH:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartEMPTYdown.png"),
                                               (config.SCALE, config.SCALE))
            elif self.direction == Direction.EAST:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartEMPTYright.png"),
                                               (config.SCALE, config.SCALE))
            elif self.direction == Direction.WEST:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartEMPTYleft.png"),
                                               (config.SCALE, config.SCALE))
        elif self.state == CartState.FULL:
            if self.direction == Direction.NORTH:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartFULLup.png"),
                                               (config.SCALE, config.SCALE))
            elif self.direction == Direction.SOUTH:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartFULLdown.png"),
                                               (config.SCALE, config.SCALE))
            elif self.direction == Direction.EAST:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartFULLright.png"),
                                               (config.SCALE, config.SCALE))
            elif self.direction == Direction.WEST:
                image = pygame.transform.scale(pygame.image.load("images/cart/shoppingcartFULLleft.png"),
                                               (config.SCALE, config.SCALE))
        rect = pygame.Rect(
            (self.position[0] + self.render_offset_x) * config.SCALE - (camera.position[0] * config.SCALE),
            (self.position[1] + self.render_offset_y) * config.SCALE - (camera.position[1] * config.SCALE),
            config.SCALE, config.SCALE)
        screen.blit(image, rect)

    def can_interact(self, player):
        return player.curr_cart != self and can_interact_default(self, player)

    def update_position(self, x_position, y_position):
        if self.direction == Direction.NORTH:
            self.position[0] = x_position+0.05
            self.position[1] = y_position-0.85
        elif self.direction == Direction.SOUTH:
            self.position[0] = x_position+0.05
            self.position[1] = y_position+0.45
        elif self.direction == Direction.EAST:
            self.position[0] = x_position+0.65
            self.position[1] = y_position
        elif self.direction == Direction.WEST:
            self.position[0] = x_position-0.8
            self.position[1] = y_position

    def collision(self, obj, x_position, y_position):
        return overlap(self.position[0], self.position[1], self.width, self.height,
                           x_position, y_position, obj.width, obj.height)

    def can_toggle(self, player):
        return player.direction == self.direction and can_interact_default(self, player, 0.3)







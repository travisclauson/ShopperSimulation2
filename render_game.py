import pygame
import config

# right now the rendering functions aren't part of a class, not sure if that goes against python etiquette :/


def render_money(screen, camera, player):
    textbox = pygame.transform.scale(pygame.image.load("text/textboxsmall.png"),
                                     (int(100), int(60)))
    screen.blit(textbox, (int(525), int(0)))
    text = render_text("$" + str(player.budget), False, (0, 0, 0))
    screen.blit(text, (540, 23))


def render_objects_and_players(screen, camera, objects, players, carts, baskets):
    to_render = sorted(players + objects, key=lambda x: x.position[1])
    for obj in to_render:
        if obj in players:
            obj.render(screen, camera, carts)
        else:
            obj.render(screen, camera)


def render_decor(screen, camera):
    window = pygame.transform.scale(pygame.image.load("images/decor/window.png"),
                                    (int(2.6 * config.SCALE), int(1.5 * config.SCALE)))
    screen.blit(window, (int(15.6 * config.SCALE) - (camera.position[0] * config.SCALE),
                         int(.25 * config.SCALE) - (camera.position[1] * config.SCALE)))
    arrow_sign = pygame.transform.scale(pygame.image.load("images/decor/arrow.png"),
                                        (int(0.5 * config.SCALE), int(.4 * config.SCALE)))
    screen.blit(arrow_sign, (int(1.5 * config.SCALE) - (camera.position[0] * config.SCALE),
                             int(.8 * config.SCALE) - (camera.position[1] * config.SCALE)))
    doormat = pygame.transform.scale(pygame.image.load("images/decor/doormat.png"),
                                     (int(config.SCALE), int(config.SCALE)))
    screen.blit(doormat, (int(0 * config.SCALE) - (camera.position[0] * config.SCALE),
                          int(15 * config.SCALE) - (camera.position[1] * config.SCALE)))
    exit_mat = pygame.transform.scale(pygame.image.load("images/decor/exit_mat.png"),
                                      (int(config.SCALE), int(config.SCALE)))
    screen.blit(exit_mat, (int(0 * config.SCALE) - (camera.position[0] * config.SCALE),
                           int(7 * config.SCALE) - (camera.position[1] * config.SCALE)))
    screen.blit(exit_mat, (int(0 * config.SCALE) - (camera.position[0] * config.SCALE),
                           int(3 * config.SCALE) - (camera.position[1] * config.SCALE)))


# Rendering map
def render_map(screen, camera, player, tile_map):
    camera.determine_camera(player, tile_map)

    # library for text map
    map_tile_image = {
        # top and bottom
        "V": pygame.transform.scale(pygame.image.load("images/floor_wall/ul_corner.png"), (config.SCALE, config.SCALE)),
        "U": pygame.transform.scale(pygame.image.load("images/floor_wall/ur_corner.png"), (config.SCALE, config.SCALE)),
        "v": pygame.transform.scale(pygame.image.load("images/floor_wall/bl_corner.png"), (config.SCALE, config.SCALE)),
        "u": pygame.transform.scale(pygame.image.load("images/floor_wall/br_corner.png"), (config.SCALE, config.SCALE)),
        "M": pygame.transform.scale(pygame.image.load("images/floor_wall/u_wall.png"), (config.SCALE, config.SCALE)),
        "m": pygame.transform.scale(pygame.image.load("images/floor_wall/b_floor.png"), (config.SCALE, config.SCALE)),

        "B": pygame.transform.scale(pygame.image.load("images/floor_wall/b_wall2.png"), (config.SCALE, config.SCALE)),
        "W": pygame.transform.scale(pygame.image.load("images/floor_wall/b_wall.png"), (config.SCALE, config.SCALE)),
        "Y": pygame.transform.scale(pygame.image.load("images/floor_wall/floor_wall.png"),
                                    (config.SCALE, config.SCALE)),
        "X": pygame.transform.scale(pygame.image.load("images/floor_wall/b_wall3.png"), (config.SCALE, config.SCALE)),

        "F": pygame.transform.scale(pygame.image.load("images/floor_wall/floor.png"), (config.SCALE, config.SCALE)),
        "L": pygame.transform.scale(pygame.image.load("images/floor_wall/L_wall_floor.png"),
                                    (config.SCALE, config.SCALE)),
        "R": pygame.transform.scale(pygame.image.load("images/floor_wall/R_wall_floor.png"),
                                    (config.SCALE, config.SCALE)),

        "0": pygame.transform.scale(pygame.image.load("images/floor_wall/floor.png"), (config.SCALE, config.SCALE)),
        "1": pygame.transform.scale(pygame.image.load("images/floor_wall/extra_1.png"), (config.SCALE, config.SCALE)),
        "2": pygame.transform.scale(pygame.image.load("images/floor_wall/extra_2.png"), (config.SCALE, config.SCALE))
    }

    y_pos = 0
    for line in tile_map:
        x_pos = 0
        for tile in line:
            image = map_tile_image[tile]
            rect = pygame.Rect(x_pos * config.SCALE - (camera.position[0] * config.SCALE),
                               y_pos * config.SCALE - (camera.position[1] * config.SCALE),
                               config.SCALE, config.SCALE)
            screen.blit(image, rect)
            x_pos = x_pos + 1
        y_pos = y_pos + 1


def render_interactions(game, screen, objects):
    for player in game.players:
        if player.render_inventory:
            player.render_items(screen, game.carts, game.baskets)
        if player.render_shopping_list:
            player.render_list(screen, game.carts, game.baskets)

    for object in objects:
        object.render_interaction(game, screen)


# not being used right now
def render_pickup(screen):
    textbox = pygame.transform.scale(pygame.image.load("text/textbox.png"),
                                     (int(640), int(150)))
    screen.blit(textbox, (int(0 * config.SCALE), int(330)))
    text = render_text("Your number has been called.", False, (0, 0, 0))
    screen.blit(text, (17, 380))


def render_text(string, bold, color):
    font = pygame.font.Font("text/pokemonfont.ttf", 17)
    if bold:
        font.bold = True
    text = font.render(string, True, color)
    return text


def render_textbox(screen, text):
    textbox = pygame.transform.scale(pygame.image.load("text/textbox.png"),
                                     (int(640), int(150)))
    screen.blit(textbox, (int(0 * config.SCALE), config.SCREEN_HEIGHT-150))
    split_text = text.split(" ")
    x_coord = 0
    y_coord = config.SCREEN_HEIGHT - 100
    for word in split_text:
        candidate_x = x_coord+17*(1 + len(word))
        if candidate_x > 623:
            y_coord += 30
            x_coord = 0
        text = render_text(" " + word, False, (0, 0, 0))
        screen.blit(text, (x_coord, y_coord))
        x_coord += 17*(1+len(word))

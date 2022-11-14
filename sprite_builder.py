import pygame
import random
from pathlib import Path

def build_sprites(player_num, sheet_filename=None):
    # loads all sprite sheets, returns two random ones
    sprite_sheet = load_sheets(player_num, sheet_filename)
    sprites = splice_and_merge([48, 72], sprite_sheet)
    return sprites


def pick_sprites(sprite_sheets):
    rand_sheet = sprite_sheets[random.randint(0, 9)]
    return rand_sheet


def load_sheets(player_num, sheet_path=None):
    sprite_sheets = []
    if sheet_path is None:
        my_path = Path("images/sprites/sprite_sheets")
        files = [str(f) for f in Path(my_path).iterdir() if f.match("*.png")]
        return pygame.image.load(files[player_num])
    else:
        return pygame.image.load(sheet_path)


def splice_and_merge(size, sheet, pos=(0, 24)):
    len_sprt_x, len_sprt_y = size  # sprite size
    sprt_rect_x, sprt_rect_y = pos  # where to find first sprite on sheet
    sheet_rect = sheet.get_rect()
    sprites = []
    for i in range(0, sheet_rect.height - len_sprt_y, size[1]):  # rows

        for i in range(0, sheet_rect.width - len_sprt_x, size[0]):  # columns

            sheet.set_clip(pygame.Rect(sprt_rect_x, sprt_rect_y, len_sprt_x, len_sprt_y))  # find sprite you want
            sprite = sheet.subsurface(sheet.get_clip())  # grab the sprite you want
            sprites.append(sprite)
            sprt_rect_x += len_sprt_x

        sprt_rect_y += len_sprt_y
        sprt_rect_x = 0
    return sprites

def splice_and_merge2(size, sheet1, sheet2, pos=(0, 24)):
    len_sprt_x, len_sprt_y = size  # sprite size
    sprt_rect_x, sprt_rect_y = pos  # where to find first sprite on sheet
    sheet_rect = sheet1.get_rect()
    sprites = []
    for i in range(0, sheet_rect.height - len_sprt_y, size[1]):  # rows

        for i in range(0, sheet_rect.width - len_sprt_x, size[0]):  # columns

            sheet1.set_clip(pygame.Rect(sprt_rect_x, sprt_rect_y, len_sprt_x, len_sprt_y))  # find sprite you want
            sprite = sheet1.subsurface(sheet1.get_clip())  # grab the sprite you want

            sprites.append(sprite)
            sprt_rect_x += len_sprt_x

        sprt_rect_y += len_sprt_y
        sprt_rect_x = 0
    return sprites
# steps for sprite building
# randomly choose two sprite sheets (head and torso)
# start building (24 images-- 6 images per direction)
#   using above code to splice head and body, then other code to merge the two and save as one image,
#   append to correct north/south/east/west array

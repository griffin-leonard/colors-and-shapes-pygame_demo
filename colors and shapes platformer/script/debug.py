import pygame as pg
from script.settings import *

def draw_debug(game):
    # camera box borders
    pg.draw.rect(game.game_surface, 'red', \
        pg.Rect(game.game_surface.get_width()//2 -CAMERA_BOX_SIZE[0]//2, \
                game.game_surface.get_height()//2 -CAMERA_BOX_SIZE[1]//2, \
                CAMERA_BOX_SIZE[0], CAMERA_BOX_SIZE[1]), 1)
    
    # croshair 
    pg.draw.line(game.game_surface, 'blue', (RES[0]//2, RES[1]//2 -20), (RES[0]//2,  RES[1]//2 +20))
    pg.draw.line(game.game_surface, 'blue', (RES[0]//2 -20, RES[1]//2), (RES[0]//2 +20,  RES[1]//2))

    # player position
    text = pg.font.Font(None, 24).render(f'player pos: ({game.player.rect.x}, {game.player.rect.y})', True, (0,0,0))
    game.game_surface.blit(text, (60,10))

    # player velocity
    text = pg.font.Font(None, 24).render(f'player vel: <{int(game.player.x_vel)}, {int(game.player.y_vel)}>', True, (0,0,0))
    game.game_surface.blit(text, (60,30))

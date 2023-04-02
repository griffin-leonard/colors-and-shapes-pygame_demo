# author: Griffin Leonard
# data created: 3/14/2023
# title: Colors and Shapes (placeholder title)
# description: a platformer about changing colors and shapes to solve puzzles

import pygame as pg, sys
from time import monotonic # for calculating delta time
from script.settings import *
from script.player import Player
from script.level import Level

class Game():
    def __init__(self):
        # set up clock  
        self.clock = pg.time.Clock()
        self.prev_time = monotonic() # for calculating delta time

        # set up display
        display_info = pg.display.Info()
        display_size = (display_info.current_w, round(display_info.current_w *RES[1]/RES[0])) # match display aspect ratio to game aspect ratio
        self.screen =  pg.display.set_mode(display_size, flags=pg.SCALED, vsync=1)
        pg.display.set_caption('Colors and Shapes')     
        if FULLSCREEN: pg.display.toggle_fullscreen()

        # set up game surface (scaled to display size)
        self.game_surface = pg.Surface(RES)   
        
        self.images = {} # maps .png filenames to pygame.Surface objects
        self.sounds = {} # maps .mp3 filenames to pygame.Sound objects
        
        # load level
        self.active_checkpoint = None # set when start Level is initialized
        self.level = Level(self, START_LEVEL)
        self.levels = {self.level.name: self.level} # maps .tmx filenames to Level objects

        # create player 
        self.player = Player(self.level, self.level.name)
        self.player.respawn(self.active_checkpoint)

        # position game camera
        self.camera_offset = (self.player.rect.centerx -self.game_surface.get_width()//2, self.player.rect.centery -self.game_surface.get_height()//2)     

    def load_level(self, filename):
        ''' creates and a new Level object.
        modifies self.level (active level)
        levels saved in self.levels dict 
        
        called when player interacts with a portal, shifts level, or respawns '''
        ### clean up old level
        for sprite in self.level.creatures.sprites(): 
            # reset creature animations
            sprite.end_animation() 
            sprite.animate(0)
        self.level.particles.empty() # remove particles 
        
        ### load new level
        if filename not in self.levels.keys():
            self.levels[filename] = Level(self, filename) # load new level for the first time
        self.level = self.levels[filename] # load previously loaded level
        self.player.level = self.level # update player's level attribute

        for sprite in self.level.inactive: sprite.reset() # reset inactive objects
        for key in self.player.keys: self.level.decorative_objs.add(key) # add collected keys to decorative group. only reset keys when respawning
        
    def run(self):
        while True:
            self.check_events() # clears event queue each frame prevents crashes
            delta_time = self.update_time() # update clock and get delta time
            self.level.run(delta_time) # update and draw current level

    def check_events(self):
        ''' checks if game has been stopped and 
        clears event queue each frame prevents crashes '''
        for event in pg.event.get(): # clearing event queue each frame prevents crashes
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN and event.key == K_RESET:
                self.player.kill()

    def update_time(self):
        self.clock.tick(FPS) # cap framerate at FPS

        # get delta time
        delta_time = monotonic() - self.prev_time # use time module for more accurate delta time 
        self.prev_time = monotonic()

        return delta_time

    def scroll_screen(self, target):
        ''' scroll the screen to follow the target object '''
        self.camera_offset = (
            max(min(self.camera_offset[0], target.rect.left - self.game_surface.get_width()//2 + CAMERA_BOX_SIZE[0]//2), target.rect.right - self.game_surface.get_width()//2 - CAMERA_BOX_SIZE[0]//2),
            max(min(self.camera_offset[1], target.rect.top - self.game_surface.get_height()//2 + CAMERA_BOX_SIZE[1]//2), target.rect.bottom - self.game_surface.get_height()//2 - CAMERA_BOX_SIZE[1]//2)
        )

    def load_image(self, filename):
        try: return self.images[filename]
        except: 
            self.images[filename] = pg.image.load(f'img/{filename}.png').convert_alpha()
            return self.images[filename]
        
    def play_sound(self, filename):
        if SOUND:
            try: self.sounds[filename].play()
            except: 
                self.sounds[filename] = pg.mixer.Sound(f'sound/{filename}.mp3')
                self.sounds[filename].play()

if __name__ == '__main__':
    pg.init() # initialize pygame
    Game().run() # create and run a new Game 
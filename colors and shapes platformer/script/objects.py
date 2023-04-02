import pygame as pg
from random import random, randint
import numpy as np
from script.sprites import *
from script.player import Player
from script.utilities import scale_vector

# Objects
class Spike(Sprite):
    def __init__(self, level, pos, color='white'):
        super().__init__(level, 'spike', pos, color)
        self.set_obj_attributes(deadly=True)
        
        # randomize image direction
        if random() < .5: self.image = pg.transform.flip(self.image, 1, 0)
        if random() < .5: self.image = pg.transform.flip(self.image, 0, 1)

class Platform(Sprite):
    ''' solid object player cannot move through '''
    def __init__(self, level, pos, width, height, color):
        pg.sprite.Sprite.__init__(self)
        self.level = level
        self.set_obj_attributes(solid=True, interactable=False)

        # get image and set color
        self.get_colored_image('platform', color, FG_RGB_SHIFT)

        self.w, self.h = width, height
        self.x, self.y = pos # top left corner
        if self.w != TILE_SIZE or self.h != TILE_SIZE: # scale image if needed
            self.image = pg.transform.scale(self.image, (int(self.w), int(self.h)))
        self.rect = self.image.get_rect(topleft=pos) 

class Checkpoint(Sprite):
    def __init__(self, level, pos, color, active=True):
        super().__init__(level, 'checkpoint', pos, color)
        self.set_obj_attributes()
        self.active = active

        # rotation
        self.rotate_speed = 100
        self.base_image = self.image # to stop memory leaks when rotating (pygame makes images bigger when rotating)
        self.angle = 0 # for more precise rotation using deltatime
        
    def update(self, dt):
        if self.active == True:
            # rotate image
            self.angle = (self.angle +self.rotate_speed*dt) % 360
            self.image = pg.transform.rotate(self.base_image, round(self.angle))
            self.rect = self.image.get_rect(center=self.rect.center)

class Portal(AnimatedSprite):
    ''' can teleport player to a level 
    self.state is the portal's color'''
    def __init__(self, level, pos, color): 
        _frames = 1
        _animation_speed = 0
        super().__init__(level, 'portal', {color: [0, _frames, _animation_speed]}, (54,64), pos, color)
        self.set_obj_attributes()

    def interact(self, interacting_obj):
        if type(interacting_obj) == Player: 
            self.level.game.load_level(self.state)
            self.level.game.play_sound('level_change')

class Orb(AnimatedSprite):
    ''' collectable orb.
    self.state is the orb's color '''
    def __init__(self, level, pos, color): 
        ''' self.state coresponds to the color of the orb. 'white' is the default color '''
        _frames = 4
        _animation_speed = 5
        super().__init__(level, 'orb', {color: [0, _frames, _animation_speed]}, (32,32), pos, color)
        self.set_obj_attributes()

    def interact(self, interacting_obj):
        if  type(interacting_obj) == Player: 
            self.level.interactive_objs.remove(self)
            self.level.inactive.add(self)
            interacting_obj.add_color(self.state)

    def reset(self):
        self.level.inactive.remove(self)
        self.level.interactive_objs.add(self)

class Key(AnimatedSprite):
    ''' collectable key '''
    def __init__(self, level, pos, color):
        _frames = 4
        _animation_speed = 3
        super().__init__(level, 'key', {color: [0, _frames, _animation_speed]}, (40,24), pos, color)
        self.set_obj_attributes()
        self.spawn_pos = pos
        self.speed = MAX_PLAYER_SPEED/2
        self.follow_radii = (TILE_SIZE*2//3, TILE_SIZE*3//2)  # [min_dis, max_dis]
        self.follow_obj = None

    def update(self, dt):
        super().update(dt) # update animation

        if self.follow_obj != None:
            dx, dy = np.array(self.follow_obj.rect.center) - np.array(self.rect.center)
            dis = np.linalg.norm((dx,dy))
            if dis <= self.follow_radii[0]: return
            elif dis > self.follow_radii[1] +self.speed*dt: 
                dx, dy = scale_vector(dx, dy, dis -self.follow_radii[1])
            else: 
                dx, dy = scale_vector(dx, dy, self.speed*dt)
            self.move(1, dx, dy) # delta time already accounted for

    def interact(self, interacting_obj):
        if type(interacting_obj) == Player: 
            self.level.game.play_sound('key')
            # change groups
            self.level.interactive_objs.remove(self)
            self.level.decorative_objs.add(self)

            self.follow_obj = interacting_obj
            interacting_obj.keys.append(self)

    def reset(self):
        self.follow_obj = None
        self.rect.center = self.spawn_pos
        self.level.decorative_objs.remove(self)
        self.level.interactive_objs.add(self)
        self.set_pos(self.spawn_pos)

class Door(Sprite):
    def __init__(self, level, pos, color):
        super().__init__(level, 'door', pos, color)
        self.set_obj_attributes(solid=True)
    
    def interact(self, player):
        ''' unlock door if player has key of same color '''
        if type(player) != Player: raise TypeError('Door.interact() takes a Player object as an argument')
        
        # check for key
        if player.keys: 
            for key in player.keys:
                if key.color == self.color: 
                    # unlock door
                    self.level.game.play_sound('unlock')
                    player.keys.remove(key)
                    self.kill()
                    key.kill()

class Bouncer(AnimatedSprite):
    ''' bouncer creature.
    bounces player if they're the same color, attacks them otherwise '''
    def __init__(self, level, pos, color): 
        _animation_data = {
            color: [0, 1, 0],
            color+'-bounce': [0, 3, 10],
            color+'-attack': [1, 3, 10],
            }
        super().__init__(level, 'bouncer', _animation_data, (32,32), pos, color)
        self.set_obj_attributes(creature=True)
        self.action = False # if True, bouncer is bouncing or attacking
        self.bounce_vel = BOUNCE_VEL

        # randomize direction for attack animation
        if random() < .5: 
            for frame in self.animations[self.color+'-attack'][1]:
                frame = pg.transform.flip(frame, 1, 0)

    def interact(self, interacting_obj):
        if type(interacting_obj) == Player: 
            if not self.action:
                self.action = True
                if interacting_obj.color == self.color: self.bounce(interacting_obj)
                else: self.attack(interacting_obj)

    def end_animation(self):
        self.action = False
        self.set_animation_state(self.color)
        self.image = self.animations[self.state][1][int(self.frame)]

    def bounce(self, target):
        self.set_animation_state(self.color+'-bounce')
        
        # bounce target
        target.in_air = True
        self.level.game.play_sound('jump')
        
        pressed = pg.key.get_pressed()
        target.y_vel = -self.bounce_vel 
        if pressed[K_JUMP]: target.y_vel -= self.bounce_vel//3
        
        # create particles
        for i in range(-1, 2):
            Particle(self.level, (self.rect.centerx +12*i, self.rect.bottom), self.color, vel=(0, -randint(80,100)), animation_speed=20, gravity=GRAVITY//2)

    def attack(self, target):
        self.set_animation_state(self.color+'-attack')
        target.kill()

    def animate(self, dt):
        if 'bounce' in self.state or 'attack' in self.state:
            animation_speed = self.animations[self.state][0]
            frames = len(self.animations[self.state][1])
            self.frame += animation_speed*dt # animation_speed * delta_time
            if self.frame >= frames: self.end_animation() # stop animation after 1 cycle
            self.image = self.animations[self.state][1][int(self.frame)]

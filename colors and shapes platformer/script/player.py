import pygame as pg
import numpy as np
import random
from script.settings import *
from script.sprites import AnimatedSprite, Particle
from script.utilities import replace_pixels, rotate_vector, scale_vector

class Player(AnimatedSprite):
    def __init__(self, level, color, shape='circle'):
        _animation_data = {
            'circle': [0, 1, 0],
            'star': [1, 5, 5]
            }
        super().__init__(level, 'player', _animation_data, PLAYER_SIZE, (0,0), state=shape+'-'+color, color=color)
        self.shape = shape
        
        # horizontal movement
        self.x_vel = 0 # horizontal velocity

        # for jumping
        self.y_vel = 0 # vertical velocity
        self.jump_timer = 0 # counts down to zero, then resets when on ground
        self.in_air = True # whether a player is currently jumping or falling

        self.respawning = False # whether player is currently respawning
        self.dead = False # whether player is dead
        self.pause = 0 # timer that counts down to zero. used for death animation, respawning, etc.
        self.keys = [] # keys collected by player

    def get_colored_animations(self, spritesheet_name, animation_data, color):
        ''' get individual images for each frame of all the animations for this object
        in every color (color argument is unused )
        save in a dict (self.animations) mapping animation states (str) to a list.
        format of list for each animation state [animation_speed, [frame1, frame2, ...]] '''
        self.animations = {} # format: {'state': [animation_speed, [img1, img2, ...]]}

        # get animation for each color
        for i, color in enumerate(COLORS.keys()):
            
            # load spritesheet of the correct color
            if color == 'white': colored_spritesheet = self.level.game.load_image(spritesheet_name)
            else: 
                colored_name = spritesheet_name+'-'+color
                try: # load colored spritesheet if it has already been loaded
                    colored_spritesheet = self.level.game.load_image(colored_name) 
                except: # create colored spritesheet if it has not been loaded
                    colored_spritesheet = self.level.game.load_image(spritesheet_name)
                    colored_spritesheet = replace_pixels(colored_spritesheet, COLORS[color], COLORS['white'])
                    self.level.game.images[colored_name] = colored_spritesheet

            # get animation for each state in each color
            for state, data in animation_data.items():
                row, frames, animation_speed = data
                self.animations[state+'-'+color] = [animation_speed, []]

                # get images for animation frames
                for frame in range(frames):
                    frame_name = spritesheet_name+f'-{state}-{i*len(animation_data) +row}-{frame}' # naming convention for animation frame images in Game.images
                    try: self.animations[state+'-'+color][1].append(self.level.game.images[frame_name])
                    except: 
                        self.level.game.images[frame_name] = colored_spritesheet.subsurface( \
                            (frame*(self.w+SPRITESHEET_SPACING), row*(self.h+SPRITESHEET_SPACING), self.w, self.h))
                        self.animations[state+'-'+color][1].append(self.level.game.images[frame_name])

    def update(self, dt):
        ''' for player controls in platforming room (Room_Platform) '''
        if self.dead: 
            self.kill()
            return # don't update if dead
        if self.respawning:
            self.respawn(self.level.game.active_checkpoint)
            return # don't update while respawning

        super().update(dt) # updates animation
        pressed = pg.key.get_pressed()

        # shift level
        if self.shape == 'star' and self.color != self.level.name and pressed[K_LVL_CHANGE]:
            self.level.game.load_level(self.color) # change level to current color
            self.level.game.play_sound('level_change')

        # update velocity
        self.apply_x_acceleration(pressed) 
        self.apply_y_acceleration(pressed)

        # apply movement and interact with objects
        self.solid_collision_check(dt, self.x_vel, self.y_vel) # check for collisions with solid objects
        self.interactive_collision_check() # interact with interactive objects 

    def apply_x_acceleration(self, keys_pressed):
        dir = keys_pressed[K_RIGHT] - keys_pressed[K_LEFT] # direction of movement. 1 = right, -1 = left, 0 = none
        
        if not dir: # if not moving, apply friction
            self.x_vel = np.sign(self.x_vel) * max(abs(self.x_vel) - self.level.x_friction, 0) 
            return
        
        if dir == np.sign(self.x_vel):
            # see settings.py for description of acceleration curve
            # acceleration is inversely proportional to speed
            curr_acc = PLAYER_SPEED *(1 - (abs(self.x_vel)-PLAYER_SPEED_OFFSET)/MAX_PLAYER_SPEED)**PLAYER_SPEED_EXPONENT
        else: # if changing direction, apply lowest acceleration
            curr_acc = PLAYER_SPEED 

        self.x_vel = max(-MAX_PLAYER_SPEED, min(MAX_PLAYER_SPEED, self.x_vel + dir*curr_acc))

    def apply_y_acceleration(self, keys_pressed):
        self.apply_gravity()
        self.jump(keys_pressed)
        
    def jump(self, keys_pressed, jump_vel=PLAYER_JUMP_VEL):
        # initiate jump
        if not self.in_air and keys_pressed[K_JUMP]:
            self.in_air = True
            self.jump_timer = PLAYER_JUMP_TIME
            self.level.game.play_sound('jump')

            # create particles
            for i in range(random.randint(-1,0), random.randint(0,1)+1):
                Particle(self.level, (self.rect.centerx -4*i, self.rect.bottom), self.color, vel=(100*i -self.x_vel/2, -random.randint(250,300)))
        
        # use jump timer to set y-velocity
        if self.jump_timer > 0 and keys_pressed[K_JUMP]:
            # jump velocity inversely proportional to time spent jumping
            self.y_vel = jump_vel/PLAYER_JUMP_TIME**10 *(PLAYER_JUMP_TIME-self.jump_timer)**PLAYER_JUMP_EXPONENT -jump_vel
            
            self.y_vel *= 1 + abs(self.x_vel)/MAX_PLAYER_SPEED*(PLAYER_JUMP_VEL_COEF-1) # use x velocity to scale jump velocity
            self.jump_timer -= 1
        
        else: self.jump_timer = 0 # reset jump timer when jump button is released

    def solid_collision_check(self, dt, dx, dy):
        ''' same as Sprite.solid_collision_check, but also accounts for jumping '''
        # check for horizontal collisions
        if dx:
            self.move(dt, dx, 0)
            collided = pg.sprite.spritecollide(self, self.level.solid_objs, 0) 
            for sprite in collided:
                if self.level.interactive_objs.has(sprite): sprite.interact(self)

                # collision to the right
                if self.rect.right > sprite.rect.left and self.rect.right < sprite.rect.right:
                    self.rect.right = sprite.rect.left
                    self.x = self.rect.left
                    self.x_vel = 0 # cancel built momentum when hitting wall
                # collision to the left
                elif self.rect.left < sprite.rect.right and self.rect.left > sprite.rect.left:
                    self.rect.left = sprite.rect.right
                    self.x = self.rect.left
                    self.x_vel = 0 # cancel built momentum when hitting wall

        # check for vertical collisions
        if dy:
            self.move(dt, 0, dy)
            collided = pg.sprite.spritecollide(self, self.level.solid_objs, 0) 
            if collided:
                for sprite in collided:
                    # collision with ceiling
                    if self.rect.top < sprite.rect.bottom and self.rect.top > sprite.rect.top:
                        self.rect.top = sprite.rect.bottom
                        self.y = self.rect.top
                        self.y_vel = 0
                        self.jump_timer = 0 # reset jump timer when hitting ceiling

                    # collision with floor
                    elif self.rect.bottom > sprite.rect.top and self.rect.bottom < sprite.rect.bottom:
                        self.rect.bottom = sprite.rect.top
                        self.y = self.rect.top
                        self.y_vel = 0
                        self.in_air = False # on ground
                        self.jump_timer = 0 # reset jump timer when on ground
            else: self.in_air = True

    def interactive_collision_check(self):
        ''' checks for collisions with deadly and interactable objects '''
        collided = pg.sprite.spritecollide(self, self.level.interactive_objs, 0) 
        for sprite in collided: 
            sprite.interact(self)
            if sprite.deadly: break # so death sound only plays once

    def kill(self):
        ''' plays death animation then pauses screen for a short time before respawning. '''
        if not self.dead:
            self.dead = True # stop drawing player
            self.level.game.play_sound('death')

            # create particles
            for x_dir in range(4): # randomize x velocity of particle
                vel = (random.randint(200,400)*(-1)**x_dir, 0)
                for angle in range(3): # randomize angle of particle velocity
                    vel = rotate_vector(vel, random.randint(0,90) * (-1)**angle)
                    vel = (vel[0] +self.x_vel/3, vel[1] +self.y_vel/3) # add player's x velocity to particle's x velocity
                    self.particle = Particle(self.level, (self.rect.centerx, self.rect.centery), self.color, vel, 20, self.level.gravity/4)
        
        # reset level after death particles disappear
        elif not self.level.particles.has(self.particle):
            if not self.pause: self.pause = DEATH_PAUSE # in frames
            self.pause -= 1
            if not self.pause: 
                self.dead = False
                self.respawn(self.level.game.active_checkpoint)

    def respawn(self, active_checkpoint):
        ''' plays respawn animation. 
        resets player's color, velocity, and keys.
        moves player position to active checkpoint and sets camera position '''
        if not self.respawning:
            self.respawning = True
            self.pause = RESPAWN_PAUSE
            self.level.game.play_sound('spawn')
            self.level.game.load_level(active_checkpoint.state) # load level with active checkpoint

            # reset player color
            self.set_color(active_checkpoint.state)

            # reset player position to spawn position
            self.set_pos((active_checkpoint.rect.centerx -PLAYER_SIZE[0]/2, active_checkpoint.rect.centery -PLAYER_SIZE[1]/2))

            # reset player movement
            self.x_vel, self.y_vel = 0, 0
            self.jump_timer = 0
            self.in_air = True

            # clear player's keys
            for key in self.keys: key.reset()
            self.keys = []

            # update caemera positon
            self.level.game.camera_offset = (self.rect.centerx -self.level.game.game_surface.get_width()//2, self.rect.centery -self.level.game.game_surface.get_height()//2)

        # create particles
        for i in range(5):
            pos = rotate_vector((CHECKPOINT_RADIUS, 0), -active_checkpoint.angle -90*i)
            vel = scale_vector(-pos[0], -pos[1], 80)
            pos = (pos[0] +active_checkpoint.rect.centerx, pos[1] +active_checkpoint.rect.centery)
            Particle(self.level, pos, active_checkpoint.color, vel, -10, 0)
        self.pause -= 1
        if not self.pause: self.respawning = False # draw player again

    def add_color(self, color):
        ''' blends the given color with the player's current color. '''
        # check if the input color is valid
        if color not in COLORS:
            raise ValueError(f"Invalid color: {color}")
        elif color == 'white' or self.color == color: # color doesn't change 
            return
        elif self.color == 'white':
            self.set_color(color)
        else:
            # combine the two colors by averaging the RGB values
            combined_rgb = tuple((a + b) // 2 for a, b in zip(COLORS[self.color], COLORS[color]))

            # find the closest color in the color map to the combined color
            self.set_color( min(COLORS, key=lambda x: sum((a - b)**2 for a, b in zip(COLORS[x], combined_rgb))) )

    def set_color(self, color):
        self.color = color
        name = self.state.split('-') # [shape, color] OR [shape, state, color]
        name = name[0]+'-'+self.color if len(name) == 2 else name[0]+'-'+name[1]+'-'+self.color 
        self.set_animation_state(name, self.frame)

    def draw(self, surf, offset):
        if not self.dead and not self.respawning: super().draw(surf, offset, [])
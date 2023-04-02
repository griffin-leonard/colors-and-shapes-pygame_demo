import pygame as pg
import numpy as np
from script.settings import *
from script.utilities import replace_pixels

class Sprite(pg.sprite.Sprite):
    def __init__(self, level, image_name, pos, color='white', rgb_shift=0):
        super().__init__()
        self.level = level
        self.state = color
        self.color = color

        self.get_colored_image(image_name, color, rgb_shift) # get object image
        self.rect = self.image.get_rect(topleft=pos) 
        self.w, self.h = self.rect.size
        self.x, self.y = pos # update using delta time for more accurate position 
        self.x_vel, self.y_vel = 0, 0

    def get_colored_image(self, image_name, color='white', rgb_shift=0):
        ''' get image and set color.
        white is the default sprite color.
        rgb_shift: value by which to change RGB values in image (for lighter or darker colors) ''' 
        # default color
        if color == 'white': 
            self.image = self.level.game.load_image(image_name)
            return
        
        try: # load colored image 
            self.image = self.level.game.load_image(image_name+'-'+color)    
        except: # create colored image if it doesn't exist yet
            self.image = self.level.game.load_image(image_name)

            # get RGB tuple from color string
            if color == 'orange': rgb_shift = int(rgb_shift*ORANGE_SHIFT_COEF)
            if rgb_shift: color = (min(255, max(0, rgb+rgb_shift)) for rgb in COLORS[color]) # shift color brighter or darker
            else: color = COLORS[color]
            
            self.image = replace_pixels(self.image, color, C_WHITE)

    def set_obj_attributes(self, solid=False, interactable=True, deadly=False, creature=False):
        self.deadly = deadly # used by Player.interactive_collision_check
        if solid: self.level.solid_objs.add(self)
        if interactable: 
            if creature: self.level.creatures.add(self)
            self.level.interactive_objs.add(self)

    def set_pos(self, pos):
        self.x, self.y = pos
        self.rect.topleft = (round(self.x), round(self.y))

    def move(self, dt, dx, dy):
        self.x += dx*dt
        self.y += dy*dt
        self.rect.topleft = (round(self.x), round(self.y))

    def apply_gravity(self):
        ''' modifies y_vel. does NOT move sprite '''
        self.y_vel += self.level.gravity

    def solid_collision_check(self, dt, dx, dy):
        # check for horizontal collisions
        if dx:
            self.move(dt, dx, 0)
            collided = pg.sprite.spritecollide(self, self.level.solid_objs, 0) 
            for sprite in collided:
                # collision to the right
                if self.rect.right > sprite.rect.left and self.rect.right < sprite.rect.right:
                    self.rect.right = sprite.rect.left
                    self.x = self.rect.left
                # collision to the left
                elif self.rect.left < sprite.rect.right and self.rect.left > sprite.rect.left:
                    self.rect.left = sprite.rect.right
                    self.x = self.rect.left

        # check for vertical collisions
        if dy:
            self.move(dt, 0, dy)
            collided = pg.sprite.spritecollide(self, self.level.solid_objs, 0) 
            for sprite in collided:
                # collision with ceiling
                if self.rect.top < sprite.rect.bottom and self.rect.top > sprite.rect.top:
                    self.rect.top = sprite.rect.bottom
                    self.y = self.rect.top
                    self.y_vel = 0
                # collision with floor
                elif self.rect.bottom > sprite.rect.top and self.rect.bottom < sprite.rect.bottom:
                    self.rect.bottom = sprite.rect.top
                    self.y = self.rect.top
                    self.y_vel = 0

    def interact(self, interacting_obj):
        if self.deadly and self.color != interacting_obj.color: interacting_obj.kill()

    def draw(self, surf, offset, views):
        if views: 
            for view in views: # only draw object if in current view
                if self.rect.colliderect(view):
                    surf.blit(self.image, (self.rect.x -offset[0], self.rect.y -offset[1]))
                    return
        
        elif self.rect.colliderect(surf.get_rect(topleft=offset)): # not in room, draw object if it collides with the screen
            surf.blit(self.image, (self.rect.x -offset[0], self.rect.y -offset[1]))


class AnimatedSprite(Sprite):
    def __init__(self, level, spritesheet_name, animation_data, size, pos, state=None, color=None, rgb_shift=0):
        pg.sprite.Sprite.__init__(self)
        self.level = level
        if color != None: self.color = color
        else: self.color = state # sprites with 1 animation state use a color as their state name

        self.w, self.h = size
        self.state = state # current animation state. if None, defaults to first animation in animation_data
        if rgb_shift: self.get_colored_animations(spritesheet_name, animation_data, self.color, rgb_shift)
        else: self.get_colored_animations(spritesheet_name, animation_data, self.color)

        # current frame in animation to draw. a negative animation speed means the animation starts at the last frame
        print(self.animations)
        if np.sign(self.animations[self.state][0]) == -1: self.frame = len(self.animations[self.state][1]) -.01
        else: self.frame = 0 

        self.image = self.animations[self.state][1][int(self.frame)] 
        self.rect = self.image.get_rect(topleft=pos) 
        self.x, self.y = pos # update using delta time for more accurate position 

    def get_colored_animations(self, spritesheet_name, animation_data, color='white', rgb_shift=0):
        ''' get individual images for each frame of all the animations for this object
        and set the correct color
        save in a dict (self.animations) mapping animation states (str) to a list.
        format of list for each animation state [animation_speed, [frame1, frame2, ...]] '''
        # load spritesheet
        try: 
            spritesheet = self.level.game.load_image(spritesheet_name+'-'+color)    
        except:
            spritesheet = self.level.game.load_image(spritesheet_name)
            spritesheet_name += '-'+color

            # # change color if needed TODO: rgb shifting
            # if rgb_shift: rgb = (min(max(0, rgb +rgb_shift), 255) for rgb in COLORS[color]) # shift color brighter or darker
            # else: rgb = COLORS[color]
            # if color != 'white': spritesheet = replace_pixels(spritesheet, rgb, COLORS['white'])

            # change color if needed
            if color != 'white': spritesheet = replace_pixels(spritesheet, COLORS[color], COLORS['white'])

        # get animation frames 
        self.animations = {} # format: {'state': [animation_speed, [img1, img2, ...]]}
        for state, data in animation_data.items():
            if self.state == None: self.state = state # default state is first state in animation_data
            row, frames, animation_speed = data
            self.animations[state] = [animation_speed, []] # format: [animation_speed, [frame1, frame2, ...]]

            # get an image for each frame of the animation
            for frame in range(frames): 
                frame_name = spritesheet_name+f'-{row}-{frame}' # naming convention for animation frame images in Game.images
            
                # get image from Game.images if it's already been loaded
                try: self.animations[state][1].append(self.level.game.images[frame_name])
                
                # if not, get it from spritesheet and save in Game.images
                except: 
                    self.level.game.images[frame_name] = spritesheet.subsurface( \
                        (frame*(self.w+SPRITESHEET_SPACING), row*(self.h+SPRITESHEET_SPACING), self.w, self.h))
                    self.animations[state][1].append(self.level.game.images[frame_name])

    def update(self, dt):
        self.animate(dt)

    def animate(self, dt):
        animation_speed = self.animations[self.state][0]
        frames = len(self.animations[self.state][1])
        self.frame += animation_speed*dt # animation_speed * delta_time
        if self.frame >= frames: self.frame = 0 # loop animation for positive animation_speed
        elif self.frame < 0: self.frame = frames -.001 # loop animation for negative animation_speed
        self.image = self.animations[self.state][1][int(self.frame)]

    def set_animation_state(self, state, frame=0):
        self.state = state
        self.frame = frame
        self.animate(0)

# class Creature(AnimatedSprite):
#     def __init__(self, level, spritesheet_name, animation_data, size, pos, state=None, rgb_shift=0):
#         super().__init__(level, spritesheet_name, animation_data, size, pos, state)


# Particles
class Particle(AnimatedSprite):
    def __init__(self, level, pos, color, vel=(0,0), animation_speed=30, gravity=GRAVITY):
        '''*pos = center of particle, not top left corner '''
        self.frames = 6
        self.animation_speed = animation_speed
        super().__init__(level, 'particle', {color: [0, self.frames, self.animation_speed]}, (PARTICLE_RADUIS*2, PARTICLE_RADUIS*2), pos, color, rgb_shift=FG_RGB_SHIFT)
        self.level.particles.add(self)
        self.set_pos((self.x -PARTICLE_RADUIS, self.y -PARTICLE_RADUIS)) # set pos to center of particle
        self.age = 0
        self.x_vel, self.y_vel = vel
        self.gravity = gravity

    def update(self, dt):
        super().update(dt)
        self.age += abs(self.animation_speed)*dt

        # kill particle after it's finished animating
        if self.age > self.frames: 
            self.kill()
            return
        
        self.apply_gravity()
        self.move(dt, self.x_vel, self.y_vel)

    def apply_gravity(self):
        ''' modifies y_vel. does NOT move sprite '''
        self.y_vel += self.gravity
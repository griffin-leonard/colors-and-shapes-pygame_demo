##### GAME SETTINGS #####
import pygame as pg

### GENERAL ###
DEBUG = True
SOUND = True
FULLSCREEN = False
START_LEVEL = 'white'
FPS = 60 # frames per second

# (in pixels)
RES = (1600, 900) # gets scaled to display size
CAMERA_BOX_SIZE = RES[0]//4, RES[1]//4 # width and height of camera box. clamps to player
TILE_SIZE = 32 
SPRITESHEET_SPACING = 4 # DO NOT CHANGE. spacing between frames in spritesheet
SPAWN_POS = (544, 384)


### KEY BINDINGS ###
K_JUMP = pg.K_SPACE
K_LEFT = pg.K_a
K_RIGHT = pg.K_d
K_LVL_CHANGE = pg.K_LSHIFT
K_RESET = pg.K_r


### PHYSICS ###

## Player 
# running 
# player starts off with a quick acceleration which rapidly decays as they reach their max speed
MAX_PLAYER_SPEED = 400 # maximum speed (in px/frame)
PLAYER_SPEED = MAX_PLAYER_SPEED/5 # initial horizontal acceleration (in px/square frame)
PLAYER_SPEED_OFFSET = PLAYER_SPEED # offset to player's x-acceleration curve. high values make player accelerate faster at all speeds
PLAYER_SPEED_EXPONENT = 4 # exponent of player's x-acceleration curve. high values make player accelerate faster at low speeds and slower at high speeds (increases decay rate)

# jumping
# player starts off with a quick acceleration which rapidly decays as they reach the peak of their jump
PLAYER_JUMP_VEL = 300 # upward acceleration applied at beginning of a jump (in px/square frame)
PLAYER_JUMP_TIME = FPS//3 # time that upward acceleration is applied for a jump (in frames)
PLAYER_JUMP_VEL_COEF = max(1.25, 1) # the ammount by which to multiply the player's y-velocity during a jump when at max running speed. 1 is the lowest possible value
PLAYER_JUMP_EXPONENT = 6 # exponent of player's jump curve

## Bouncers
BOUNCE_VEL = PLAYER_JUMP_VEL*2

## Level
# scalars (not vector)
GRAVITY = abs(30) # downward acceleration (in px/square frame). applied every frame.
X_FRICTION = abs(PLAYER_SPEED) # friction (in px/square frame). applied to player's x-velocity when not accelerating.


### GRAPHICS ###
# sizes (in pixels)
PLAYER_SIZE = (32, 32) 
PARTICLE_RADUIS = 6 # for centering particles
CHECKPOINT_RADIUS = 48 # for respawning animation

# timers
# time to pause (in frames)
DEATH_PAUSE = FPS//3 # after player death
RESPAWN_PAUSE = FPS*3//5 # before player respawn

# colors
C_WHITE = (230, 220, 215)
C_BACKGROUND = (255, 255, 255)
COLORS = {
    'white': C_WHITE,
    'red': (225, 0, 0),
    'orange': (255, 128, 0),
    'yellow': (225, 225, 0),
    'green': (0, 225, 0),
    'blue': (0, 0, 255),
    'indigo': (128, 0, 255),
    'violet': (255, 0, 255),
    'brown': (128, 64, 0)
}

# color shifts
# the ammount by which to change each RGB value for each color
FG_RGB_SHIFT = -127  # foreground (includes platforms)
BG_RGB_SHIFT = 128 # background
WHITE_FG_SHIFT = 0 # foreground when level is white (includes platforms)
ORANGE_SHIFT_COEF = 1/4 # the ammount by which to multiply the shift values for orange 



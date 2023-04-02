import numpy as np
from math import sin, cos, pi

def replace_pixels(img, color, replace=(0,0,0)):
    ''' Swap one color for another in an image, preserve transparency.
    args:
        img: pygame.Surface
        color: RGB tuple of new color
        replace: RGB tuple of color to replace '''
    img = img.copy()
    w, h = img.get_size()
    r, g, b = color
    for x in range(w):
        for y in range(h):
            pixel = img.get_at((x, y))
            if pixel[:3] == replace:
                img.set_at((x, y), (r, g, b, pixel[3]))
    return img

def scale_vector(dx, dy, size):
    ''' takes a change in x and y values (in pixels), 
    scales them to to new size, and return '''
    try: angle = np.arctan(dy/dx) # in radians
    except: 
        if dy == 1: angle = pi/2
        elif dy == -1: angle = pi*3/2
        else: angle = 0
    sign_x = np.sign(dx)
    sign_y = np.sign(dy)
    return sign_x*size*abs(cos(angle)), sign_y*size*abs(sin(angle))

def rotate_vector(vec, theta):
    ''' takes a vector and rotates it by theta degrees clockwise. '''
    vec = np.array(vec)
    theta = np.deg2rad(theta)
    rot = np.array(((cos(theta), -sin(theta)), (sin(theta), cos(theta))))
    return np.dot(rot, vec)
from pytmx.util_pygame import load_pygame # for loading tmx files
from script.settings import *
from script.objects import *
from script.sprites import Particle
from script.debug import draw_debug

class Level():
    def __init__(self, game, filename):
        ''' load a level from a tmx file, create objects, and add them to the appropriate groups '''
        self.name = filename # color 
        self.game = game

        # physics attributes
        self.gravity = GRAVITY
        self.x_friction = X_FRICTION

        # create object groups
        self.solid_objs = pg.sprite.Group() # player and creatures can't pass through these
        self.interactive_objs = pg.sprite.Group() # player can interact with these
        self.creatures = pg.sprite.Group() # also in interactive_objs group. take special action when changing level
        self.decorative_objs = pg.sprite.Group() # non-interactive objects
        self.inactive = pg.sprite.Group() # objects that are not currently active (e.g. collected Orbs)
        self.particles = pg.sprite.Group()
        
        # create objects and add them to groups
        self.views = {} # camera bounds. key: view name, value: pg.Rect
        self.get_objects_from_tmx(filename)

        ## use color shift settings to get level colors 
        # background 
        color_shift = BG_RGB_SHIFT
        if filename == 'orange': color_shift = int(color_shift*ORANGE_SHIFT_COEF)
        self.bg_color = tuple(min(255, rgb+color_shift) for rgb in COLORS[filename])
        
        # foreground
        color_shift = FG_RGB_SHIFT
        if filename == 'white': color_shift = 0
        elif filename == 'orange': color_shift = int(color_shift*ORANGE_SHIFT_COEF)
        self.fg_color = tuple(min(255, max(0, rgb+color_shift)) for rgb in COLORS[filename])
        
    def get_objects_from_tmx(self, filename):
        ''' load level data from tmx file,
        use it to create objects,
        and add them to the appropriate groups. '''
        # filename is a color string
        tmx_data = load_pygame('level/'+filename+'.tmx') 

        for layer in tmx_data.layers: 
            # create objects in level
            if layer.name == 'Objects':
                for obj in layer:
                    if obj.type == 'Platform':
                        Platform(self, (obj.x, obj.y), obj.width, obj.height, filename)
                    elif obj.type == 'Checkpoint':
                        sprite = Checkpoint(self, (obj.x, obj.y), filename)
                        self.game.active_checkpoint = sprite
                    else:
                        if obj.type == None: raise ValueError(f"Invalid object type in level \'{filename}\'.\nCheck object Class in Tiled.")
                        sprite = eval(obj.type + '(self, (obj.x, obj.y), obj.name)' ) # create object
            
            # get views (camera bounds for various rooms)
            elif layer.name == 'Views':
                for obj in layer:
                    if obj.name not in self.views.keys(): self.views[obj.name] = [pg.Rect(obj.x, obj.y, obj.width, obj.height)]
                    else: self.views[obj.name].append(pg.Rect(obj.x, obj.y, obj.width, obj.height))
            
    def run(self, delta_time):
        self.update(delta_time)
        self.draw(self.game.screen, self.game.game_surface, self.game.camera_offset, self.game.player)

    def update(self, delta_time):
        # update level objects
        self.decorative_objs.update(delta_time)  
        self.solid_objs.update(delta_time) 
        self.interactive_objs.update(delta_time) 
        self.game.player.update(delta_time) 
        self.particles.update(delta_time) 
        
        self.game.scroll_screen(self.game.player) # update camera (clamps to player)

    def draw(self, screen, game_surface, camera_offset, player):
        views = self.get_view(player) # get view that player is in
        if views:
            game_surface.fill(self.fg_color) # draw foreground (color of platforms)
            for view in views:
                fill_rect = view.copy()
                fill_rect.x -= camera_offset[0]
                fill_rect.y -= camera_offset[1]
                game_surface.fill(self.bg_color, fill_rect) 
        else:
            game_surface.fill(self.bg_color) # draw background

        # draw game objects
        for sprite in self.solid_objs.sprites(): sprite.draw(game_surface, camera_offset, views)
        for sprite in self.interactive_objs.sprites(): sprite.draw(game_surface, camera_offset, views)
        for sprite in self.decorative_objs.sprites(): sprite.draw(game_surface, camera_offset, views)
        player.draw(game_surface, camera_offset) 
        for sprite in self.particles.sprites(): sprite.draw(game_surface, camera_offset, views)

        if DEBUG: draw_debug(self.game)

        # scale game_surface to display size and update display
        pg.transform.smoothscale(game_surface, (screen.get_width(), screen.get_height()), screen)
        pg.display.update() 

    def get_view(self, player):
        ''' returns the view that the player is in
        as list of pg.Rects '''
        # get current view(s)
        views = []
        for l in self.views.values():
            if player.rect.collidelist(l) != -1: views += l
        return views
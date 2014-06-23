#!/usr/bin/env python

import random, os.path

#import basic pygame modules
import pygame
from pygame.locals import *
from pygame.surface import Surface

main_dir = os.path.split(os.path.abspath(__file__))[0]


SCREENRECT     = Rect(0, 0, 640, 480)
GRID_SIZE      = 32

blocks_positions = []

shots = pygame.sprite.Group()
bombs = pygame.sprite.Group()
blocks = pygame.sprite.Group()
player_group = pygame.sprite.Group()


for i in range(1,(SCREENRECT.width/32)-1):
    blocks_positions.append((i*32,0))
    blocks_positions.append((i*32,448))

for i in range(SCREENRECT.height/32):
    blocks_positions.append((0,i*32))
    blocks_positions.append((608,i*32))


def load_image(file):
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    return surface

def load_images(image_names):
    images = []
    for name in image_names:
        images.append(load_image(name))
    return images

class Scenario(object):
    blocks_undestroyable=[]
    blocks_destroyable=[]
    explosions = []

    @classmethod
    def collision_solid(cls,obj):
        for i in cls.blocks_undestroyable + cls.blocks_destroyable:
            if i.rect.colliderect(obj.bbox):
                return True
        return False

    @classmethod
    def collision_explosion(cls,obj):
        for i in cls.explosions:
            if i.rect.colliderect(obj.bbox):
                return True
        return False


class Bomb(pygame.sprite.Sprite):
    defaultlife = 170
    explosion_range = 2
    images = []
    def __init__(self, player):
        super(Bomb,self).__init__()
        self.player = player
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.move_ip(player.rect.x+ player.rect.width/2, player.rect.y+ player.rect.height)
        self.rect.x = GRID_SIZE*(self.rect.x/GRID_SIZE)
        self.rect.y = GRID_SIZE*(self.rect.y/GRID_SIZE)
        self.life = self.defaultlife
        bombs.add([self])
        self.layer = 1

    def update(self):
        self.life = self.life - 1
        if self.life <= 0: self.explode()

    def explode(self):

        BombExplosion(self, 0 ,0)
        for i in range(1,self.explosion_range):
            BombExplosion(self, -i,0)
        for i in range(1,self.explosion_range):
            BombExplosion(self, i,0)
        for i in range(1, self.explosion_range):
            BombExplosion(self, 0,i)
        for i in range(1, self.explosion_range):
            BombExplosion(self, 0,-i)
        self.player.bombnum -= 1
        self.kill()


class BombExplosion(pygame.sprite.DirtySprite):
    defaultlife = 27
    animcycle = 3
    images = []

    def __init__(self, bomb, xdis, ydis):
        super(BombExplosion,self).__init__()
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=bomb.rect.center)
        self.rect.move_ip(xdis*self.rect.width, ydis*self.rect.height)
        self.life = self.defaultlife
        Scenario.explosions.append(self)
        self.layer = 1
        bombs.add(self)

    def update(self):
        self.life = self.life - 1
        if self.life <= 0: self.kill()

    def kill(self):
        Scenario.explosions.remove(self)
        super(BombExplosion,self).kill()


class BlockUndestroyable(pygame.sprite.DirtySprite):
    image_file = 'block_undestroyable.png'
    image = None
    def __init__(self, x, y):
        # Mirar que son los contenedores
        pygame.sprite.Sprite.__init__(self)
        if not BlockUndestroyable.image:
            BlockUndestroyable.image = load_image(BlockUndestroyable.image_file)
        self.image = BlockUndestroyable.image
        self.rect = self.image.get_rect()
        self.rect.move_ip(x, y)
        self.layer = 1

class BlockDestroyable(pygame.sprite.DirtySprite):
    image_file = 'block_destroyable.png'
    image = None
    def __init__(self, x, y):
        # Mirar que son los contenedores
        pygame.sprite.Sprite.__init__(self)
        if not BlockDestroyable.image:
            BlockDestroyable.image = load_image(BlockDestroyable.image_file)
        self.image = BlockDestroyable.image
        self.rect = self.image.get_rect()
        self.rect.move_ip(x, y)
        self.layer = 1

    def update(self):
        for i in Scenario.explosions:
            if i.rect.colliderect(self.rect):
                Scenario.blocks_destroyable.remove(self)
                self.kill()
                return

from pygame.sprite import Sprite
class Player(pygame.sprite.DirtySprite):
    speed = 4
    bounce = 24
    gun_offset = -11
    images_up = load_images(['DELANTE1.png','DELANTE2.png','DELANTE3.png'])
    images_down = load_images(['DETRAS1.png','DETRAS2.png','DETRAS3.png'])
    images_left = load_images(['IZQ1.png','IZQ2.png','IZQ3.png'])
    images_right = load_images(['DER1.png','DER2.png','DER3.png'])
    max_bombs = 4
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_list = Player.images_down
        self.image = self.image_list[0]
        self.image_index = 0
        self.rect = Rect(0,0,28,28)
        self.bbox = Rect(10,29,27,26)
        self.rect.move_ip(32,32)
        self.bbox.move_ip(32,32)
        self.layer = 0
        self.reloading = 0
        self.facing = -1
        self.bombnum = 0

    def move(self, hdirection, vdirection):

        if hdirection:
            self.facing = hdirection
        self.bbox.move_ip(hdirection*self.speed, 0)
        self.rect.move_ip(hdirection*self.speed, 0)
        if Scenario.collision_solid(self):
            self.rect.move_ip(-hdirection*self.speed,0)
            self.bbox.move_ip(-hdirection*self.speed,0)
        self.rect.move_ip(0,vdirection*self.speed)
        self.bbox.move_ip(0,vdirection*self.speed)
        if Scenario.collision_solid(self):
            self.rect.move_ip(0,-vdirection*self.speed)
            self.bbox.move_ip(0,-vdirection*self.speed)
        self.rect = self.rect.clamp(SCREENRECT)
        self.bbox = self.bbox.clamp(SCREENRECT)
        if vdirection > 0:
            self.image_index = (self.image_index + 1) % (len(self.image_list)*4)
            self.image_list = Player.images_up
        elif vdirection < 0:
            self.image_index = (self.image_index + 1) % (len(self.image_list)*4)
            self.image_list = Player.images_down
        elif hdirection < 0:
            self.image_index = (self.image_index + 1) % (len(self.image_list)*4)
            self.image_list = Player.images_left
        elif hdirection > 0:
            self.image_index = (self.image_index + 1) % (len(self.image_list)*4)
            self.image_list = Player.images_right
        self.image = self.image_list[self.image_index/4]

    def update(self):
        if Scenario.collision_explosion(self):
            self.kill()

    def set_bomb(self):
        if self.bombnum < self.max_bombs:
            new_bomb = Bomb(self)
            self.bombnum +=1


class Explosion(pygame.sprite.DirtySprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife
        self.layer = 1

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0:
            self.kill()



class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "Score: %d" % SCORE
            self.image = self.font.render(msg, 0, self.color)


def create_random_blocks(num):
    blocks = []
    for i in range(num):
        rand_x =  int((random.random()*18)+1)*GRID_SIZE
        rand_y =  int((random.random()*13)+1)*GRID_SIZE
        if rand_x <= 2*GRID_SIZE and rand_y <= 2*GRID_SIZE:
            rand_x = 3*GRID_SIZE
        blocks.append(BlockDestroyable(rand_x,rand_y))
    return blocks

def main(winstyle = 0):
    pygame.init()

    winstyle = 0
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    img = load_image('bomberman_down.png')
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    Bomb.images = [load_image('bomb.png')]
    BombExplosion.images = [load_image('bomb_explosion.png')]

    pygame.display.set_caption('Pygame Bomberman')
    pygame.mouse.set_visible(0)

    bgdtile = load_image('background.gif')
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    global SCORE
    player = Player()

    player_group.add(player)
    #Create Some Starting Values
    global score
    kills = 0
    clock = pygame.time.Clock()

    #initialize our starting sprites

    Scenario.blocks_undestroyable = []
    for block_pos in blocks_positions:
        new_block = BlockUndestroyable(block_pos[0],block_pos[1])
        Scenario.blocks_undestroyable.append(new_block)
        blocks.add(new_block)

    destroyable_blocks = create_random_blocks(270)
    for i in destroyable_blocks:
        Scenario.blocks_destroyable.append(i)
        blocks.add(i)

    while True:

        #get input
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
        keystate = pygame.key.get_pressed()

        # clear/erase the last drawn
        screen.fill((255,255,255))
        screen.blit(background,(0,0))
        bombs.draw(screen)
        bombs.update()
        blocks.draw(screen)
        blocks.update()
        player_group.draw(screen)
        player_group.update()

        hdirection = keystate[K_RIGHT] - keystate[K_LEFT]
        vdirection = keystate[K_DOWN] -  keystate[K_UP]
        player.move(hdirection, vdirection)
        place_bomb = keystate[K_SPACE]
        if not player.reloading and place_bomb:
            player.set_bomb()
        player.reloading = place_bomb
        pygame.display.flip()

        clock.tick(40)

    pygame.time.wait(1000)
    pygame.quit()


main()


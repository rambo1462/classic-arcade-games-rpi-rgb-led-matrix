#!/usr/bin/env python
from typing import Dict, List
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw
import time
import sys
import random
import termios
import atexit
from select import select
import threading

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.chain_length = 1
options.parallel = 1
options.scan_mode = 0
options.hardware_mapping = 'adafruit-hat'  # If you have regular: 'regular' or an Adafruit HAT: 'adafruit-hat'
options.brightness = 50
matrix = RGBMatrix(options = options)

class KBHit:
    def __init__(self):
        # Save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)
        # New terminal setting unbuffered
        self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)
        # Support normal-terminal reset at exit
        atexit.register(self.set_normal_term)
    def set_normal_term(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)
    def getch(self):
        s = ''
        return sys.stdin.read(1)
    def getarrow(self):
        c = sys.stdin.read(3)[2]
        vals = [65, 67, 66, 68]
        return vals.index(ord(c))
    def kbhit(self):
        dr,dw,de = select([sys.stdin], [], [], 0)
        return dr != []

# board size is (x2-x1)-2 by (y2-y1)-2
bounds = {
    'x1' : 11,
    'y1' : 9,
    'x2' : 20,
    'y2' : 29
}

board_x_length = (bounds['x2']-bounds['x1'])-2
board_y_length = (bounds['y2']-bounds['y1'])-2

blocks = {
    1: [15, (bounds['y1']+1), 16, (bounds['y1']+1), 17, (bounds['y1']+1), 16, (bounds['y1']+2)],
    2: [15, (bounds['y1']+1), 16, (bounds['y1']+1), 17, (bounds['y1']+1), 17, (bounds['y1']+2)],
    3: [15, (bounds['y1']+1), 16, (bounds['y1']+1), 16, (bounds['y1']+2), 17, (bounds['y1']+2)],
    4: [16, (bounds['y1']+1), 16, (bounds['y1']+2), 17, (bounds['y1']+1), 17, (bounds['y1']+2)],
    5: [15, (bounds['y1']+2), 16, (bounds['y1']+2), 16, (bounds['y1']+1), 17, (bounds['y1']+1)],
    6: [15, (bounds['y1']+2), 15, (bounds['y1']+1), 16, (bounds['y1']+1), 17, (bounds['y1']+1)],
    7: [15, (bounds['y1']+1), 16, (bounds['y1']+1), 17, (bounds['y1']+1), 18, (bounds['y1']+1)]
}

class Block:
    def __init__(self, type, r, g, b, count):
        self.type = type
        self.block = blocks.get(type).copy()
        self.r = r
        self.g = g
        self.b = b
        self.rotate_count = count
    def fall_down(self):
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], 0, 0, 0)
        for i in range(0, 8, 2):
            self.block[i+1] += 1
            matrix.SetPixel(self.block[i], self.block[i+1], self.r, self.g, self.b)
    def go_left(self):
        global ground
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], 0, 0, 0)
            self.block[i] -= 1
        if hit_ground(self, ground):
            for i in range(0, 8, 2):
                self.block[i] += 1
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], self.r, self.g, self.b)
    def go_right(self):
        global ground
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], 0, 0, 0)
            self.block[i] += 1
        if hit_ground(self, ground):
            for i in range(0, 8, 2):
                self.block[i] -= 1
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], self.r, self.g, self.b)
    def rotate(self):
        if self.type == 4:
            return
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], 0, 0, 0)
        if self.type == 1:
            if self.rotate_count == 0:
                self.block[4] -= 1
                self.block[5] -= 1
            elif self.rotate_count == 1:
                self.block[6] += 1
                self.block[7] -= 1
            elif self.rotate_count == 2:
                self.block[0] += 1
                self.block[1] += 1
            elif self.rotate_count == 3:
                self.block[0] -= 1
                self.block[1] -= 1
                self.block[4] += 1
                self.block[5] += 1
                self.block[6] -= 1
                self.block[7] += 1
        elif self.type == 2:
            if self.rotate_count == 0:
                self.block[0] += 1
                self.block[1] -= 1
                self.block[4] -= 1
                self.block[5] += 1
                self.block[6] -= 2
            elif self.rotate_count == 1:
                self.block[0] += 1
                self.block[1] += 1
                self.block[4] -= 1
                self.block[5] -= 1
                self.block[7] -= 2
            elif self.rotate_count == 2:
                self.block[0] -= 1
                self.block[1] += 1
                self.block[4] += 1
                self.block[5] -= 1
                self.block[6] += 2
            elif self.rotate_count == 3:
                self.block[0] -= 1
                self.block[1] -= 1
                self.block[4] += 1
                self.block[5] += 1
                self.block[7] += 2
        elif self.type == 3:
            if self.rotate_count == 0 or self.rotate_count == 2:
                self.block[0] += 2
                self.block[1] -= 1
                self.block[7] -= 1
            elif self.rotate_count == 1 or self.rotate_count == 3:
                self.block[0] -= 2
                self.block[1] += 1
                self.block[7] += 1
        elif self.type == 5:
            if self.rotate_count == 0 or self.rotate_count == 2:
                self.block[0] += 1
                self.block[1] -= 2
                self.block[2] += 1
            elif self.rotate_count == 1 or self.rotate_count == 3:
                self.block[0] -= 1
                self.block[1] += 2
                self.block[2] -= 1
        elif self.type == 6:
            if self.rotate_count == 0:
                self.block[1] -= 2
                self.block[2] += 1
                self.block[3] -= 1
                self.block[6] -= 1
                self.block[7] += 1
            elif self.rotate_count == 1:
                self.block[0] += 2
                self.block[2] += 1
                self.block[3] += 1
                self.block[6] -= 1
                self.block[7] -= 1
            elif self.rotate_count == 2:
                self.block[1] += 2
                self.block[2] -= 1
                self.block[3] += 1
                self.block[6] += 1
                self.block[7] -= 1
            elif self.rotate_count == 3:
                self.block[0] -= 2
                self.block[2] -= 1
                self.block[3] -= 1
                self.block[6] += 1
                self.block[7] += 1
        elif self.type == 7:
            if self.rotate_count == 0 or self.rotate_count == 2:
                self.block[0] += 2
                self.block[1] -= 2
                self.block[2] += 1
                self.block[3] -= 1
                self.block[6] -= 1
                self.block[7] += 1
            elif self.rotate_count == 1 or self.rotate_count == 3:
                self.block[0] -= 2
                self.block[1] += 2
                self.block[2] -= 1
                self.block[3] += 1
                self.block[6] += 1
                self.block[7] -= 1
        for i in range(0, 8, 2):
            matrix.SetPixel(self.block[i], self.block[i+1], self.r, self.g, self.b)
        self.rotate_count = (self.rotate_count + 1) % 4
    def __str__(self):
        blockset = set()
        for i in range(0, 8, 2):
            blockset.add((self.block[i], self.block[i+1]))
        return str(self.type) + '-' + str(blockset) + '-' + f'({self.r}, {self.g}, {self.b})'
    
def new_block():
    type = random.randrange(1, 8)
    r = 0
    g = 0
    b = 0
    while (r < 50 and g < 50 and b < 50):
        r = random.randrange(0, 255)
        g = random.randrange(0, 255)
        b = random.randrange(0, 255)
    r_count = 0
    return Block(type, r, g, b, r_count)

def out_of_bounds(x, y):
    if x < bounds['x1'] or x > bounds['x2'] or \
       y < bounds['y1'] or y > bounds['y2']:
        return True
    else:
        return False

def clear_pixels(x1, y1, x2, y2):
    for x in range(x1, x2+1):
        for y in range(y1, y2+1):
            matrix.SetPixel(x, y, 0, 0, 0)

def color_block(block):
    for i in range(0, 8, 2):
        matrix.SetPixel(block.block[i], block.block[i+1], block.r, block.g, block.b)

def clear_block(block):
    for i in range(0, 8, 2):
        matrix.SetPixel(block.block[i], block.block[i+1], 0, 0, 0)

def draw_next():
    global next
    clear_pixels(24, 10, 28, 14)
    for i in range(0, 8, 2):
        matrix.SetPixel(
            next.block[i] + 10, next.block[i+1] + 2, next.r, next.g, next.b
            )

def hit_ground(block, ground):
    for i in range(0, 8, 2):
        for xy in ground:
            if block.block[i] == xy[0] and block.block[i+1] == xy[1]:
                return True
    return False

def update_ground(ground, block):
    for i in range(0, 8, 2):
        # ground.add([x, y])
        ground.add((block.block[i], block.block[i+1] - 1)) 
    return ground

# Border
image = Image.new("RGB", (32, 32))
draw = ImageDraw.Draw(image) 
draw.rectangle((bounds['x1']-1, bounds['y1']-1, bounds['x2']+1, bounds['y2']+1), fill=(0, 0, 0), outline=(255, 255, 255))
# Next box
draw.rectangle(((23, 9), (29, 15)), fill=(0, 0, 0), outline=(255, 255, 255))
matrix.SetImage(image)

keyboard = KBHit()
count = 0

dirs = [
    'UP',  
    'RIGHT',
    'DOWN',
    'LEFT'
]

block = new_block()
next = new_block()
draw_next()

# Next Box
font = graphics.Font()
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf")
# textColor = graphics.Color(255, 255, 0)
# graphics.DrawText(matrix, font, 26, 13, textColor, 't')
# graphics.DrawText(matrix, font, 26, 19, textColor, 'x')
# graphics.DrawText(matrix, font, 26, 25, textColor, 'e')
# graphics.DrawText(matrix, font, 26, 31, textColor, 'N')

ground = set()
for i in range(bounds['x1'], bounds['x2']+1):
    ground.add((i, bounds['y2']))

def hit_key():
    global block, ground
    while True:
        if keyboard.kbhit():
            try:
                arrow_dir = dirs[keyboard.getarrow()]
                if not hit_ground(block, ground):
                    if arrow_dir == 'DOWN':
                        block.fall_down()
                    elif arrow_dir == 'LEFT':
                        block.go_left()
                    elif arrow_dir == 'RIGHT':
                        block.go_right()   
                    elif arrow_dir == 'UP':
                        block.rotate()  
            except Exception as e:
                print(e)

def main_thread():
    global block, ground, next
    while True:
        if hit_ground(block, ground):
            ground = update_ground(ground, block)
            block = next
            next = new_block()
            draw_next()
        block.fall_down()
        time.sleep(1)

hitkey = threading.Thread(target=hit_key)
main_thread = threading.Thread(target=main_thread)
hitkey.start()
main_thread.start()



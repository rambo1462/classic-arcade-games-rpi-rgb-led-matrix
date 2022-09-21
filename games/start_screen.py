#!/usr/bin/env python
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw
import time
import sys
import subprocess
import termios
import atexit
from select import select

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

class Block:
    def __init__(self, x, y, prev_x, prev_y, dir):
        self.x = x
        self.y = y
        self.prev_x = x
        self.prev_y = y
        self.dir = dir

# board size is (x2-x1)-2 by (y2-y1)-2
bounds = {
    'x1' : 1,
    'y1' : 1,
    'x2' : 30,
    'y2' : 30
}

board_x_length = (bounds['x2']-bounds['x1'])-2
board_y_length = (bounds['y2']-bounds['y1'])-2

def clear_pixels(x1, y1, x2, y2):
    for x in range(x1, x2+1):
        for y in range(y1, y2+1):
            matrix.SetPixel(x, y, 0, 0, 0)

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.chain_length = 1
options.parallel = 1
options.scan_mode = 0
options.hardware_mapping = 'adafruit-hat'  # If you have regular: 'regular' or an Adafruit HAT: 'adafruit-hat'
options.brightness = 100
matrix = RGBMatrix(options = options)

# Border
# image = Image.new("RGB", (32, 32))
# draw = ImageDraw.Draw(image) 
# draw.rectangle((bounds['x1']-1, bounds['y1']-1, bounds['x2']+1, bounds['y2']+1), fill=(0, 0, 0), outline=(255, 255, 0))
# matrix.SetImage(image)

# Title
font = graphics.Font()
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/6x10.bdf")
textColor = graphics.Color(0, 255, 0)
graphics.DrawText(matrix, font, 2, 10, textColor, 'Snak')
graphics.DrawText(matrix, font, 25, 10, textColor, 'e')
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf")


def loop(snake, r, g, b, r1, g1, b1, min, max):
    lenSnake = len(snake)
    head = snake[0]
    matrix.SetPixel(head.x, head.y, r, g, b)
    if head.x == max and head.y == max:
        head.dir = 'LEFT'
    elif head.x == max and head.y == min:
        head.dir = 'DOWN'
    elif head.x == min and head.y == max:
        head.dir = 'UP'
    elif head.x == min and head.y == min:
        head.dir = 'RIGHT'
    head.prev_x = head.x
    head.prev_y = head.y
    if head.dir is 'UP':
        head.y += -1
    elif head.dir is 'RIGHT':
        head.x += 1
    elif head.dir is 'DOWN':
        head.y += 1
    elif head.dir is 'LEFT':
        head.x += -1
    for i in range(lenSnake-1):
        segment = snake[i+1]
        if i is lenSnake-2:
            matrix.SetPixel(segment.prev_x, segment.prev_y, r1, g1, b1)
        segment.prev_x = segment.x
        segment.prev_y = segment.y
        segment.x = snake[i].prev_x
        segment.y = snake[i].prev_y

def custom_loop(snake, r, g, b, r1, g1, b1, min, max, switch):
    lenSnake = len(snake)
    head = snake[0]
    matrix.SetPixel(head.x, head.y, r, g, b)
    if head.x == 31 and head.y == 11:
        head.dir = 'LEFT'
    elif head.x == 0 and head.y == 11:
        if switch <= 100:
            head.dir = 'DOWN'
        else:
            head.dir = 'UP'
    elif head.x == max and head.y == max:
        if head.dir == 'RIGHT':
            head.dir = 'UP'
        else:
            head.dir = 'LEFT'
    elif head.x == max and head.y == min:
        if head.dir == 'RIGHT':
            head.dir = 'DOWN'
        else:
            head.dir = 'LEFT'
    elif head.x == min and head.y == max:
        if head.dir == 'LEFT':
            head.dir = 'UP'
        else:
            head.dir = 'RIGHT'
    elif head.x == min and head.y == min:
        head.dir = 'RIGHT'
    head.prev_x = head.x
    head.prev_y = head.y
    if head.dir is 'UP':
        head.y += -1
    elif head.dir is 'RIGHT':
        head.x += 1
    elif head.dir is 'DOWN':
        head.y += 1
    elif head.dir is 'LEFT':
        head.x += -1
    for i in range(lenSnake-1):
        segment = snake[i+1]
        if i is lenSnake-2:
            matrix.SetPixel(segment.prev_x, segment.prev_y, r1, g1, b1)
        segment.prev_x = segment.x
        segment.prev_y = segment.y
        segment.x = snake[i].prev_x
        segment.y = snake[i].prev_y

keyboard = KBHit()
count = 0

dirs = [
    'UP',  
    'RIGHT',
    'DOWN',
    'LEFT'
]

def createSnake(numBlocks, x, y, x1, y1, dir):
    snake = []
    for i in range(numBlocks):
        snake.append(Block(x, y, x1, y1, dir))
    return snake

snake = createSnake(70, 0, 0, 0, 0, 'RIGHT')
snake1 = createSnake(70, 31, 31, 31, 31, 'LEFT')

for i in range(len(snake)-1):
    matrix.SetPixel(snake[i].x, snake[i].y, 0, 0, 0)
    matrix.SetPixel(snake1[i].x, snake1[i].y, 0, 0, 0)

# Main Loop
while True:

    if keyboard.kbhit():
        # Start Game
        master = []
        count = 0
        for i in range(16):
            master.append(createSnake(3, i, i, i, i, 'RIGHT'))

        for i in range(200):
            if count <= 120:
                for j in range(16):
                    loop(master[j], 255, 255, 0, 255, 255, 0, j, 31-j)
            else:
                if count == 121:
                    master = []
                    for k in range(16):
                        master.append(createSnake(3, k, k, k, k, 'LEFT'))
                for x in range(16):
                    loop(master[x], 0, 0, 0, 0, 0, 0, x, 31-x)
            time.sleep(0.01)
            count += 1
        sys.exit(0)
            
    if count == 100:
        textColor = graphics.Color(255, 0, 0)
        graphics.DrawText(matrix, font, 6, 17, textColor, 'Press')
        textColor = graphics.Color(0, 0, 255)
        graphics.DrawText(matrix, font, 11, 23, textColor, 'Key')
        textColor = graphics.Color(255, 0, 0)
        graphics.DrawText(matrix, font, 4, 29, textColor, 'To')
        graphics.DrawText(matrix, font, 13, 29, textColor, 'Play')
    if count == 200:
        clear_pixels(1, 12, 30, 30)
        count = 0

    custom_loop(snake, 255, 255, 0, 0, 0, 0, 0, 31, count)
    # loop(snake1, 255, 255, 0, 0, 0, 0, 0, 31)
    
    time.sleep(0.010)
    count += 1

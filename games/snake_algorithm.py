#!/usr/bin/env python
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw
import time
import sys
import random
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
    'x1' : 4,
    'y1' : 16,
    'x2' : 27,
    'y2' : 29
}

board_x_length = (bounds['x2']-bounds['x1'])-2
board_y_length = (bounds['y2']-bounds['y1'])-2

def out_of_bounds(x, y):
    if x < bounds['x1'] or x > bounds['x2'] or \
       y < bounds['y1'] or y > bounds['y2']:
        return True
    else:
        return False

def game_over():
    print('Game Over')
    with open('/home/pi/rpi-rgb-led-matrix/bindings/python/samples/high_scores.txt','a+') as file:
        file.write(f'{score}\n')
    sys.exit()

def get_rand_exclude(snake, axis1, axis2):
    num_list = list(range(bounds[axis1], bounds[axis2]))
    if axis1 == 'x1':
        for i in range(len(snake)):
            try:
                num_list.remove(snake[i].x)
            except ValueError:
                pass
    elif axis1 == 'y1':
        for i in range(len(snake)):
            try:
                num_list.remove(snake[i].y)
            except ValueError:
                pass
    return random.choice(num_list)

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
options.brightness = 50
matrix = RGBMatrix(options = options)

# Border
image = Image.new("RGB", (32, 32))
draw = ImageDraw.Draw(image) 
draw.rectangle((bounds['x1']-1, bounds['y1']-1, bounds['x2']+1, bounds['y2']+1), fill=(0, 0, 0), outline=(255, 255, 0))
matrix.SetImage(image)

# Title
font = graphics.Font()
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/6x10.bdf")
textColor = graphics.Color(255, 255, 0)
graphics.DrawText(matrix, font, 1, 7, textColor, 'Snake')

# Scoreboard
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf")
score = 0
graphics.DrawText(matrix, font, 1, 14, textColor, 'Score')
graphics.DrawText(matrix, font, 20, 14, textColor, ':')
graphics.DrawText(matrix, font, 23, 14, textColor, f'{score}')

# Init Snake, Apple and other variables
direction = 'RIGHT'
start_pnt = (bounds['y2'] + bounds['y1']) // 2
snake = [
    Block(bounds['x1'], start_pnt, 0, 0, direction), 
    Block(bounds['x1'], start_pnt, 0, 0, direction),
    Block(bounds['x1'], start_pnt, 0, 0, direction)
]
apple = Block(get_rand_exclude(snake, 'x1', 'x2'), get_rand_exclude(snake, 'y1', 'y2'), 0, 0, 'UP')
dirs = [
    'UP',  
    'RIGHT',
    'DOWN',
    'LEFT'
]
keyboard = KBHit()
count = 0

# Draw 1st apple and snake
matrix.SetPixel(apple.x, apple.y, 0, 255, 0)
for i in range(len(snake)-1):
    matrix.SetPixel(snake[i].x, snake[i].y, 255, 0, 0)

# Main Loop
while True:
    lenSnake = len(snake)
    snakeHead = snake[0]
    matrix.SetPixel(snakeHead.x, snakeHead.y, 255, 0, 0)

    if keyboard.kbhit():
        try:
            arrow = keyboard.getarrow()
            arrow_dir = dirs[arrow]
            if direction != arrow_dir and direction != dirs[(arrow+2)%4]:
                direction = arrow_dir
        except Exception as e:
            print(e)
        finally:
            pass
        

    snakeHead.prev_x = snakeHead.x
    snakeHead.prev_y = snakeHead.y

    if direction is 'UP':
        snakeHead.y += -1
    elif direction is 'RIGHT':
        snakeHead.x += 1
    elif direction is 'DOWN':
        snakeHead.y += 1
    elif direction is 'LEFT':
        snakeHead.x += -1

    # Snake eats apple
    if snakeHead.x == apple.x and snakeHead.y == apple.y:
        score += 1
        clear_pixels(23, 9, 30, 13)
        graphics.DrawText(matrix, font, 23, 14, textColor, f'{score}')

        if score+3 == (board_x_length * board_y_length) - 1:
            print('No way, You Won')
            sys.exit(0)
        
        apple.x = get_rand_exclude(snake, 'x1', 'x2')

        apple.y = get_rand_exclude(snake, 'y1', 'y2')
        matrix.SetPixel(apple.x, apple.y, 0, 255, 0)

        tail = snake[lenSnake-1]
        snake.append(Block(tail.x, tail.y, 0, 0, tail.dir))
        

    # Snake goes out of bounds
    if out_of_bounds(snakeHead.x, snakeHead.y):
        game_over()

    for i in range(lenSnake-1):
        segment = snake[i+1]
        
        # Snake ran into self
        if count > 3:
            if snakeHead.x == segment.x and snakeHead.y == segment.y:
                game_over()

        if i is lenSnake-2:
            matrix.SetPixel(segment.prev_x, segment.prev_y, 0, 0, 0)

        segment.prev_x = segment.x
        segment.prev_y = segment.y
        segment.x = snake[i].prev_x
        segment.y = snake[i].prev_y

    time.sleep(0.1)
    count += 1

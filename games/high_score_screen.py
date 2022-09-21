#!/usr/bin/env python
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw
import time

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
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/5x7.bdf")
textColor = graphics.Color(0, 255, 0)
graphics.DrawText(matrix, font, 6, 7, textColor, 'High')
graphics.DrawText(matrix, font, 2, 13, textColor, 'Sc')
graphics.DrawText(matrix, font, 11, 13, textColor, 'ores')
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf")

def get_high_scores():
    with open('/home/pi/rpi-rgb-led-matrix/bindings/python/samples/high_scores.txt','r') as file:
        scores = []
        for line in file.readlines():
            score = line.rstrip()
            scores.append(int(score))
    scores.sort(reverse = True)
    with open('/home/pi/rpi-rgb-led-matrix/bindings/python/samples/high_scores.txt','w') as file:   
        if len(scores) >= 3: 
            for i in range(3):
                file.write(f'{scores[i]}\n')
        else:
            for score in scores:
                file.write(f'{score}\n')
    return scores


scores = get_high_scores()




# Loop
count = 0
for i in range(1200):
    for i in range(len(scores)):
        if (i == 3):
            break
        textColor = graphics.Color(count, count, count)
        graphics.DrawText(matrix, font, 12, 18+(6*i), textColor, f'{scores[i]}')
    if count >= 255:
        count -= 1
    else:
        count += 1
    if count == 0:
        count += 1
    time.sleep(0.005)
    

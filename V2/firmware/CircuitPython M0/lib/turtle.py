import math, time
#from analogio import AnalogIn
import simpleio
import board
import digitalio
import adafruit_motor.servo
import pulseio
pwm = pulseio.PWMOut(board.D5, frequency=50)


DEBUG = True

_x = 0
_y = 0
_heading = 0

# robot specific parameters
wheel_dia = 51  # mm (increase = decrease distance
wheel_base = 73.5  # mm (increase = spiral in) 
PEN_DOWN = 50   # angle of servo when pen is down
PEN_UP = 0    # angle of servo when pen is up

steps_rev = 512    # 512 for 64x gearbox, 128 for 16x gearbox
delay_time = 2   # time between steps in ms

'''
leftEmitter = digitalio.DigitalInOut(board.D10)
leftLED = digitalio.DigitalInOut(board.D7)
rightEmitter = digitalio.DigitalInOut(board.D13)
rightLED = digitalio.DigitalInOut(board.D11)
button = digitalio.DigitalInOut(board.D12)
'''

#servo = simpleio.Servo(board.D5)
servo = adafruit_motor.servo.Servo(pwm, min_pulse=750, max_pulse=2250)

'''
rightDetector = AnalogIn(board.A0)
leftDetector = AnalogIn(board.A1)

leftLED.direction = digitalio.Direction.OUTPUT
leftEmitter.direction = digitalio.Direction.OUTPUT
rightLED.direction = digitalio.Direction.OUTPUT
rightEmitter.direction = digitalio.Direction.OUTPUT
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# turn on IR
leftEmitter.value = True
rightEmitter.value = True
'''

# [wires blue->pink->yel->org]
Lstep0 = digitalio.DigitalInOut(board.A2)
Lstep1 = digitalio.DigitalInOut(board.A3)
Lstep2 = digitalio.DigitalInOut(board.A4)
Lstep3 = digitalio.DigitalInOut(board.A5)

Rstep0 = digitalio.DigitalInOut(board.SCK)
Rstep1 = digitalio.DigitalInOut(board.MOSI)
Rstep2 = digitalio.DigitalInOut(board.MISO)
Rstep3 = digitalio.DigitalInOut(board.D9)

# put connections in array to make life easier
R_stepper = [Rstep0, Rstep1, Rstep2, Rstep3]
L_stepper = [Lstep0, Lstep1, Lstep2, Lstep3]

for wire in L_stepper:
    wire.direction = digitalio.Direction.OUTPUT

for wire in R_stepper:
    wire.direction = digitalio.Direction.OUTPUT

# stepper patterns
patterns = [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]]


def setDebug(val):
    global DEBUG
    DEBUG = val
    

def step(distance):
    steps = distance * steps_rev / (wheel_dia * math.pi)
    if steps-int(steps) > 0.5:
        return int(steps + 1)
    else:
        return int(steps)


def forward(distance):
    global _x, _y, _heading
    steps = step(distance)
    if DEBUG: print('foward(%s mm) - %s steps' % (distance, steps))
    for x in range(steps):
        for pattern in range(len(patterns)):
            for bit in range(len(patterns[pattern])):  # fwd_mask[num]:
                L_stepper[bit].value = patterns[pattern][bit]
                R_stepper[bit].value = patterns[::-1][pattern][bit]
            time.sleep(delay_time/1000)

    # new point 
    deltax = distance * math.cos(math.radians(_heading))
    deltay = distance * math.sin(math.radians(_heading))
    _x = _x + deltax
    _y = _y + deltay


def backward(distance):
    global _x, _y, _heading
    steps = step(distance)
    if DEBUG: print('backward(%s mm) - %s steps' % (distance, steps))
    for x in range(steps):
        for pattern in range(len(patterns)):
            for bit in range(len(patterns[pattern])):  # fwd_mask[num]:
                R_stepper[bit].value = patterns[pattern][bit]
                L_stepper[bit].value = patterns[::-1][pattern][bit]
            time.sleep(delay_time/1000)
 
    # new point 
    deltax = distance * math.cos(math.radians(_heading - 180))
    deltay = distance * math.sin(math.radians(_heading - 180))
    _x = _x + deltax
    _y = _y + deltay


def left(degrees):
    global _x, _y, _heading
    rotation = degrees / 360.0
    distance = wheel_base * math.pi * rotation
    steps = step(distance)
    if DEBUG: print('left(%s deg.) - %s steps' % (degrees, steps))
    for x in range(steps):
        for pattern in range(len(patterns)):
            for bit in range(len(patterns[pattern])):  # fwd_mask[num]:
                R_stepper[bit].value = patterns[pattern][bit]
                L_stepper[bit].value = patterns[pattern][bit]
            time.sleep(delay_time/1000)
    _heading = _heading + degrees
    while _heading > 360:
        _heading = _heading - 360


def right(degrees):
    global _x, _y, _heading
    rotation = degrees / 360.0
    distance = wheel_base * math.pi * rotation
    steps = step(distance)
    if DEBUG: print('right(%s deg.) - %s steps' % (degrees, steps))
    for x in range(steps):
        for pattern in range(len(patterns)):
            for bit in range(len(patterns[pattern])):  # fwd_mask[num]:
                R_stepper[bit].value = patterns[::-1][pattern][bit]
                L_stepper[bit].value = patterns[::-1][pattern][bit]
            time.sleep(delay_time/1000)
    _heading = _heading - degrees
    while _heading < 0:
        _heading = _heading + 360


def penup():
	if DEBUG: print('penup()') 
	servo.angle = PEN_UP
  
  
def pendown():
	if DEBUG: print('pendown()') 
	servo.angle = PEN_DOWN

         
def done():
    if DEBUG: print('done()') 
    for value in range(4):
        L_stepper[value].value = False
        R_stepper[value].value = False
		
		
def goto(x, y):
    center_x, center_y = position()
    bearing = getBearing(x, y, center_x, center_y)
    trnRight = heading() - bearing
    #print('trnRight = %s' % trnRight)
    if abs(trnRight) > 180:
        if trnRight >= 0:
            left(360 - trnRight)
            #if DEBUG: print('left(%s)' % (360 - trnRight))
        else:
            right(360 + trnRight)
            #if DEBUG: print('right(%s)' % (360 + trnRight))
    else:
        if trnRight >= 0:
            right(trnRight)
            #if DEBUG: print('right(%s)' % trnRight)
        else:
            left(-trnRight)
            #if DEBUG: print('left(%s)' % -trnRight)
    dist = distance(tuple(position()), (x, y))
    forward(dist)
    #if DEBUG: print('forward(%s)' % dist)
	

def pensize(size):
    print('pensize() is not implemented in Turtle Robot')
    pass
   

def pencolor(color):
    print('pencolor() is not implemented in Turtle Robot')
    pass

   
def speed(x):
    print('speed() is not implemented in Turtle Robot')
    pass
    
    
def position():
    return _x, _y
    
    
def heading():
    return _heading

    
def distance(pointA, pointB):
    return abs((pointB[0] - pointA[0])**2  + (pointB[1] - pointA[1])**2)**0.5


def getBearing(x, y, center_x, center_y):
    # https://stackoverflow.com/questions/5058617/bearing-between-two-points
    angle = math.degrees(math.atan2(y - center_y, x - center_x))
    bearing = (angle + 360) % 360
    #bearing2 = (90 - angle) % 360
    #print "gb: x=%2d y=%2d angle=%6.1f bearing=%5.1f bearing2=%5.1f" % (x, y, angle, bearing1, bearing2)
    return bearing
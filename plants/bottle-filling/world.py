#!/usr/bin/env python
import socket
import sys
import time      
import math
import os
import json
import threading
import random
import pygame
import logging
import argparse
import getopt
import pymunk
from pygame.locals import *
from pygame.color import THECOLORS

from modbus import ServerModbus as Server
from modbus import REG_CONTACT, REG_LEVEL, REG_MOTOR, REG_NOZZLE, REG_RUN, REG_THROUGHPUT, REG_COLOR
from modbus import COLORS

dark_mode   = False
show_title  = False
debug       = False

# Physic world parameters
speed               = 0.25
FPS                 = 30.0
bottle_thickness    = 7
ball_radius         = 3
NEXT_BOTTLE_DISTANCE = 100
BOTTLE_SPACING = 80 + bottle_thickness 
WORLD_SCREEN_WIDTH = 550
WORLD_SCREEN_HEIGHT = 350

nozzle_center_x = 180
nozzle_top_y = 450
nozzle_width = 15
nozzle_height = 20
nozzle_throughput = 1
extra_width = 60
extra_height_top = 20 
extra_height_bottom = -10  

level_sensor_x = 172
level_sensor_y = 220
level_sensor_size = 10

sensor_x = WORLD_SCREEN_WIDTH // 3.58
sensor_y = WORLD_SCREEN_HEIGHT // 1.66
sensor_radius = 10

wheel_radius = 17
wheel_y = 280
wheels = []
wheel_angles = []
wheel_rotation_speed = 0.05
conveyor_line_offset = 0.0

# Logging
logging.basicConfig()
log = logging.getLogger()

# Globals
bottles         = []
conveyor        = None

def get_theme_colors():
    if dark_mode:
        return {
            "bg": THECOLORS["black"],           
            "text": THECOLORS["gray90"],        
            "title": THECOLORS["lightgreen"],   
            "sensor": THECOLORS["lightcoral"],  
            "polygon": THECOLORS["gray70"],     
            "line": THECOLORS["darkgreen"],    
            "ball": THECOLORS["lightgreen"]   
        }
    else:
        return {
            "bg": THECOLORS["white"],
            "text": THECOLORS["gray20"],
            "title": THECOLORS["deepskyblue"],
            "sensor": THECOLORS["red"],
            "polygon": THECOLORS["black"],
            "line": THECOLORS["dodgerblue4"],
            "ball": THECOLORS["blue"]
        }

def to_pygame(p, scale=1.0):
    return int(p.x * scale), int((-p.y + 600) * scale)

def add_ball(space, color):
    mass = 0.1 + 0.1 * color
    radius = ball_radius
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
    x = random.randint(180, 183)

    body = pymunk.Body(mass, inertia)
    body.position = x, 430

    shape = pymunk.Circle(body, radius, (0, 0))
    space.add(body, shape)
    return shape

def draw_polygon(screen, shape, scale=1.0, color=THECOLORS['black']):
    vertices = shape.get_vertices()
    points = [to_pygame(v.rotated(shape.body.angle) + shape.body.position, scale) for v in vertices]
    pygame.draw.polygon(screen, color, points)

def draw_ball(screen, ball, scale=1.0, color=THECOLORS['blue']):
    p = to_pygame(ball.body.position, scale)
    pygame.draw.circle(screen, color, p, max(1, int(ball.radius * scale)), 0)

def add_bottle(space):
    mass = 5
    inertia = 10
    #inertia = float("inf")

    body = pymunk.Body(mass, inertia, pymunk.Body.KINEMATIC)
    body.position = (130, 300)

    l1 = pymunk.Segment(body, (-150, 0), (-100, 0), bottle_thickness)      # bottle_bottom
    l2 = pymunk.Segment(body, (-150, 0), (-150, 100), bottle_thickness)    # bottle_right_side
    l3 = pymunk.Segment(body, (-100, 0), (-100, 100), bottle_thickness)    # bottle_left_side

    # Glass friction
    l1.friction = 0.9
    l2.friction = 0.9
    l3.friction = 0.9
    l1.elasticity = 0.95
    l2.elasticity = 0.95
    l3.elasticity = 0.95

    space.add(l1, l2, l3, body)
    return l1, l2, l3

def draw_lines(screen, lines, scale=1.0, color=THECOLORS['dodgerblue4']):
    for line in lines:
        body = line.body
        x = body.position.x
        if x < 130:
            alpha = max(0, (x - 100) / 30.0)  
            partial_color = (
                int(color[0] * alpha),
                int(color[1] * alpha),
                int(color[2] * alpha)
            )
        else:
            partial_color = color

        pv1 = body.position + line.a.rotated(body.angle)
        pv2 = body.position + line.b.rotated(body.angle)
        p1 = to_pygame(pv1, scale)
        p2 = to_pygame(pv2, scale)
        pygame.draw.lines(screen, partial_color, False, [p1, p2], bottle_thickness*int(scale))

def add_polygon(space, pos, size, collision_type):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = pos
    shape = pymunk.Poly.create_box(body, size)
    shape.friction = 1.0
    shape.collision_type = collision_type
    space.add(body, shape)  
    return shape

def add_nozzle(screen, scale):

    # Draw the grey area around nozzle
    nozzle_rect_color = (232, 232, 232) if not dark_mode else (50, 50, 80)
    rect_x = int((nozzle_center_x - nozzle_width - extra_width / 2) * scale)
    rect_y = int((600 - nozzle_top_y - nozzle_height - extra_height_top) * scale)
    rect_width = int((nozzle_width * 2 + extra_width) * scale)
    rect_height = int((nozzle_height + extra_height_top + (nozzle_top_y - 280) + extra_height_bottom) * scale)
    pygame.draw.rect(
        screen,
        nozzle_rect_color,
        pygame.Rect(rect_x, rect_y, rect_width, rect_height),
        border_radius=0,
        border_top_left_radius=int(48 * scale),
        border_top_right_radius=int(48 * scale)
    )

    # Draw triangle
    triangle_base_x = (nozzle_center_x + 1) * scale
    triangle_base_y = (610 - nozzle_top_y) * scale
    triangle_width = 15 * scale
    triangle_height = 11 * scale
    triangle_points = [
        (triangle_base_x, triangle_base_y + triangle_height),
        (triangle_base_x - triangle_width / 2, triangle_base_y),
        (triangle_base_x + triangle_width / 2, triangle_base_y)
    ]
    triangle_color = colors["polygon"]
    pygame.draw.polygon(screen, triangle_color, triangle_points)

    rect_color = (0, 0, 0)
    rect_x = (nozzle_center_x - 35) * scale
    rect_y = (598 - nozzle_top_y) * scale
    rect_width = 30 * scale
    rect_height = 7 * scale
    pygame.draw.rect(screen, rect_color, pygame.Rect(rect_x, rect_y, rect_width, rect_height))

    rect_x2 = (nozzle_center_x - 30.2) * scale
    rect_y2 = (601 - nozzle_top_y) * scale
    rect_width2 = 7 * scale
    rect_height2 = 7 * scale
    pygame.draw.rect(screen, rect_color, pygame.Rect(rect_x2, rect_y2, rect_width2, rect_height2))

def add_laser(screen, scale):
    screen_x = int(sensor_x * scale)
    screen_y = int(sensor_y * scale)
    line_height = int(111 * scale) 
    line_width = max(1, int(0.5 * scale)) 

    line_rect = pygame.Rect(
        screen_x - line_width // 2,
        screen_y - line_height // 2,
        line_width,
        line_height
    )
    pygame.draw.rect(screen, colors["sensor"], line_rect)

    ball_color = (255, 0, 0)
    ball_radius = 3 * scale
    ball_center_x = (nozzle_center_x - 32) * scale + 25 * scale + ball_radius + -23 * scale
    ball_center_y = (598 - nozzle_top_y + 6) * scale + 7 * scale / 2
    pygame.draw.circle(screen, ball_color, (int(ball_center_x), int(ball_center_y)), int(ball_radius))

def add_conveyor(screen, space, window_width, scale, motor_state):

    global wheel_angles
    global conveyor_line_offset
    global conveyor

    draw_polygon(screen, conveyor, scale, color=colors["polygon"])

    line_color = colors["line"]
    line_width = max(1, int(3 * scale))
    line_height = int(8 * scale)
    conveyor_rect_bottom_y = (600 - 300 + 4) * scale
    conveyor_width = conveyor.bb.right - conveyor.bb.left

    line_scroll_speed = speed if motor_state else 0.0
    conveyor_line_offset += line_scroll_speed
    spacing_px = 70
    if conveyor_line_offset >= spacing_px:
        conveyor_line_offset -= spacing_px

    num_lines = int(conveyor_width / spacing_px) + 2
    for i in range(num_lines):
        x = conveyor.bb.left + (i * spacing_px) + conveyor_line_offset 
        screen_x = int(x * scale) 
        screen_y_start = int(conveyor_rect_bottom_y - line_height) 

        pygame.draw.line(
            screen,
            line_color,
            (screen_x, screen_y_start),
            (screen_x, screen_y_start + line_height),
            line_width
        )


    for idx, wheel in enumerate(wheels):
        center = to_pygame(wheel.body.position, scale)
        radius = int(wheel.radius * scale)

        if motor_state:
            wheel_angles[idx] += wheel_rotation_speed

        border_color = THECOLORS["gray"] if dark_mode else THECOLORS["white"]
        pygame.draw.circle(screen, border_color, center, radius + 2)

        pygame.draw.circle(screen, THECOLORS["black"], center, radius)

        for s in range(6):
            angle = wheel_angles[idx] + (2 * math.pi * s / 6)
            end_x = center[0] + radius * 0.7 * math.cos(angle)
            end_y = center[1] + radius * 0.7 * math.sin(angle)
            pygame.draw.line(screen, THECOLORS["gray70"], center, (int(end_x), int(end_y)), 2)

        pygame.draw.circle(screen, THECOLORS["black"], center, radius, 2)

    # Draw wheels
    update_wheels(space, wheels, window_width, wheel_y, wheel_radius)
    if len(wheel_angles) != len(wheels):
        wheel_angles = [0.0 for _ in wheels]

def run_servers():
    def start_server(obj):
        obj.start()

    threading.Thread(target=start_server, args=(plc,), daemon=True).start()

def is_sensor_touching_bottle(sensor_x, sensor_y, sensor_radius, bottles):
    for bottle in bottles:
        left_segment = bottle[1]  
        body = left_segment.body

        world_a = body.position + left_segment.a.rotated(body.angle)
        world_b = body.position + left_segment.b.rotated(body.angle)

        ax, ay = to_pygame(world_a)
        bx, by = to_pygame(world_b)

        if abs(ax - bx) < 2:
            min_y = min(ay, by)
            max_y = max(ay, by)

            if abs(sensor_x - ax) <= sensor_radius and min_y <= sensor_y <= max_y:
                return True

    return False

def add_level_sensor(screen, scale):
    rect_x = (level_sensor_x) * scale
    rect_y = (level_sensor_y) * scale
    pygame.draw.circle(screen, THECOLORS["red"], (rect_x, rect_y) , 3, 0)

def update_wheels(space, wheels, window_width, wheel_y, wheel_radius):
    spacing = 137.5
    min_wheels = 5
    max_wheels = max(min_wheels, int(window_width / spacing) + 1)
    current_count = len(wheels)

    while len(wheels) > max_wheels:
        wheel = wheels.pop()
        for c in wheel.body.constraints:
            space.remove(c)
        space.remove(wheel, wheel.body)

    while len(wheels) < max_wheels:
        i = len(wheels)
        wheel_x = i * spacing
        mass = 1.0
        moment = pymunk.moment_for_circle(mass, 0, wheel_radius)
        wheel_body = pymunk.Body(mass, moment)
        wheel_body.position = (wheel_x, wheel_y)
        wheel_shape = pymunk.Circle(wheel_body, wheel_radius)
        wheel_shape.friction = 1.0
        wheel_shape.elasticity = 0.5
        space.add(wheel_body, wheel_shape)

        pivot = pymunk.PivotJoint(wheel_body, space.static_body, (wheel_x, wheel_y))
        pivot.collide_bodies = False
        space.add(pivot)

        spring = pymunk.DampedRotarySpring(wheel_body, space.static_body, 0.0, 2000000.0, 10000.0)
        space.add(spring)

        wheels.append(wheel_shape)

def runWorld(autorun):

    global conveyor
    global nozzle_throughput

    # Setup pygame and pymunk
    pygame.init()
    screen = pygame.display.set_mode((WORLD_SCREEN_WIDTH, WORLD_SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("VirtuaPlant - Bottle Filling Simulation")
    icone = pygame.image.load("assets/github_icon.png")
    pygame.display.set_icon(icone)
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.use_spatial_hash(ball_radius, 10000)
    space.gravity = (0.0, -900.0)

    nozzle_actuator = add_polygon(space, (181, 450), (15, 20), 0x9)
    bottles.append(add_bottle(space))
    balls = []

    running = True
    scale = 1.0

    #Add pygame events to reduce CPU usage 
    RESIZE_EVENT = pygame.event.custom_type() 
    pygame.event.set_allowed([QUIT, KEYDOWN, K_ESCAPE, RESIZE_EVENT])
    pygame.time.set_timer(pygame.event.Event(RESIZE_EVENT), 1, 1)

    level_sensor = 0
    contact = 0
    nozzle = 0
    motor = 0
    nextColor       = COLORS[0]
    currentColor    = COLORS[0]  
    run = autorun

    plc.write(REG_RUN, autorun)

    while running:

        clock.tick(FPS)

        #Handle events
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

            #Update screen size
            previous_scale = scale
            if event.type == RESIZE_EVENT:
                window_width, window_height = screen.get_size()
                scale_x = window_width / WORLD_SCREEN_WIDTH
                scale_y = window_height / WORLD_SCREEN_HEIGHT
                scale = min(scale_x, scale_y)

                fontBig = pygame.font.SysFont(None, int(40 * scale))
                fontMedium = pygame.font.SysFont(None, int(26 * scale))

                conveyor_width = window_width / scale
                if ( conveyor == None ):
                    conveyor = add_polygon(space, (conveyor_width / 2, 300), (conveyor_width, 20), 0x7)
                if (scale != previous_scale):
                    space.remove(conveyor)
                    conveyor = add_polygon(space, (conveyor_width / 2, 300), (conveyor_width, 20), 0x7)

                #Debug
                point = pygame.mouse.get_pos()
                log.info(point)
                log.info("balls:" + str(len(balls)) + "bottles:" + str(len(bottles)))
                log.info ("level=" + str(level_sensor) + " ,contact=" + str(contact) + ", nozzle=" + str(nozzle) + "motor=" + str(motor) + ", run=" + str(run) + ", throughput" + str(nozzle_throughput) + ", currentColor=" + str(currentColor))

                pygame.time.set_timer(pygame.event.Event(RESIZE_EVENT), 1000, 1)

        #Update Modbus registers
        run = plc.read(REG_RUN)
        motor = plc.read(REG_MOTOR)
        nozzle = plc.read(REG_NOZZLE)
        contact = plc.read(REG_CONTACT)
        level_sensor = plc.read(REG_LEVEL)
        nozzle_throughput = plc.read(REG_THROUGHPUT)
        nextColor = plc.read(REG_COLOR)

        # Manage PLC programm
        # Motor Logic
        if (run == 1) and ((contact == 0) or (level_sensor == 1)):
            plc.write(REG_MOTOR, 1)
        else:
            plc.write(REG_MOTOR, 0)

        # Nozzle Logic 
        if (run == 1) and ((contact == 1) and (level_sensor == 0)):
            plc.write(REG_NOZZLE, 1)
        else:
            plc.write(REG_NOZZLE, 0)

        if is_sensor_touching_bottle(sensor_x, sensor_y, sensor_radius, bottles):
            plc.write(REG_CONTACT, 1)
        else:
            plc.write(REG_CONTACT, 0)

        # Clear screen and add static elements
        screen.fill(colors["bg"])
        add_nozzle(screen, scale)
        if ( not level_sensor ):
            add_level_sensor(screen, scale)
        draw_polygon(screen, nozzle_actuator, scale, color=colors["polygon"])

        # Add title and text
        if ( show_title ):
            screen.blit(fontMedium.render("Bottle-filling factory", 1, colors["title"]), (int(10 * scale), int(10 * scale)))
            title_y = int(10 * scale)
            virtua_y = title_y + fontMedium.get_height() + int(4 * scale)
            screen.blit(fontBig.render("VirtuaPlant", 1, colors["text"]), (int(10 * scale), virtua_y))
            quit_text = fontMedium.render("(press Esc to quit)", True, colors["text"])
            screen.blit(quit_text, (window_width - quit_text.get_width() - int(10 * scale), int(10 * scale)))

        # Handle world inputs
        if nozzle:
            if bottles:
                for i in range(nozzle_throughput):
                    balls.append((add_ball(space, currentColor), bottles[-1][0].body, currentColor))
        else:
            currentColor = nextColor

        if motor:
            # Move bottle
            for bottle in bottles:
                bottle[0].body.velocity = (40*speed, 0)
        else:
            for bottle in bottles:
                bottle[0].body.velocity = (0, 0)

        if run:
            if not bottles or (bottles[-1][0].body.position.x > 130 + BOTTLE_SPACING):
                new_bottle = add_bottle(space)
                new_bottle[0].body.position = pymunk.Vec2d(130, 300)
                bottles.append(new_bottle)

        # Add laser if needed
        if not contact:
            add_laser(screen, scale)

        # Draw conveyor 
        add_conveyor(screen, space, window_width, scale, motor)

        # Handle balls
        flag_sensor_level=False
        for ball_data in balls[:]:
            ball, _ , ballColor = ball_data
            # Also move balls to avoid glitches (ball passing through bottle)
            #if motor:
            #    ball.body.position = (ball.body.position.x + speed, ball.body.position.y)

            # Detect collision with level sensor
            x,y = to_pygame(ball.body.position)
            if ( contact and not flag_sensor_level):
                if ( int(y) > level_sensor_y and int(y) < level_sensor_y + level_sensor_size ):
                    if ( ( int(x) > level_sensor_x and int(x) < level_sensor_x + level_sensor_size )):
                        if ( ball.body.velocity.y > -100.0 ):
                            plc.write(REG_LEVEL, 1)
                            flag_sensor_level=True

            if ( ball.body.position.y < 150 or ball.body.position.x > WORLD_SCREEN_WIDTH+150 or ball.body.position.x < -150):
                space.remove(ball, ball.body)
                balls.remove(ball_data)
            else:
                draw_ball(screen, ball, scale, color=COLORS[ballColor])

        if ( flag_sensor_level == False ):
            plc.write(REG_LEVEL, 0)

        # Add/remove bottles from world
        for bottle in bottles[:]:
            pos_x = bottle[0].body.position.x
            screen_pos_x = pos_x * scale
            if screen_pos_x > window_width + 1500 or bottle[0].body.position.y < 150:
                for segment in bottle:
                    space.remove(segment)
                space.remove(bottle[0].body)
                bottles.remove(bottle)
            else:
                draw_lines(screen, bottle, scale, color=colors["line"])

#       body = pymunk.Body()
#       x = 130 
#       y = 300 
#       body.position = x, y
#       p = to_pygame(body.position, scale)
#       pygame.draw.circle(screen, "red", body.position, 3, 0)

        space.step(1 / FPS)
        pygame.display.flip()

        if ( debug ): pygame.display.set_caption(f"fps: {clock.get_fps()}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="The plant")
    parser.add_argument("-i", "--ip", required=False, help="IP address", default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, required=False, help="Port", default=1502)
    parser.add_argument("-s", "--speed", type=int, required=False, help="Motor speed", default=8)
    parser.add_argument("-t", "--throughput", type=int, required=False, help="Nozzle throughput", default=2)
    parser.add_argument("-d", "--debug", action='store_true', help="Debug", default=0)
    parser.add_argument("-r", "--run", action='store_true', help="Run plant at startup", default=False)
    parser.add_argument("-D", "--dark", action='store_true', help="Dark mode", default=False)
    parser.add_argument("-S", "--show_title", action='store_true', help="Show title", default=False)
    return parser.parse_args()

def main():
    global plc
    global dark_mode
    global colors 
    global speed
    global debug
    global nozzle_throughput
    global show_title

    # Arguments
    args = parse_arguments()
    ip = args.ip
    port = args.port
    nozzle_throughput = args.throughput
    speed = speed * args.speed
    show_title = args.show_title
    autorun = args.run
    dark_mode = args.dark
    debug = args.debug
    log.setLevel(logging.WARNING)
    if ( debug ):
        log.setLevel(logging.INFO)

    colors = get_theme_colors()

    # Initialise plc component
    plc = Server(ip, port)
    run_servers()  
    log.info("Modbus server started")
    plc.write(REG_THROUGHPUT, nozzle_throughput)

    # Run World
    runWorld(autorun)    
    pygame.quit()

if __name__ == "__main__":
    main()

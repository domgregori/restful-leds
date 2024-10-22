"""
Author: Logan Steffen
Version: v1.1.0
Started: 11/01/2023
Last Updated: 04/01/2024
License: MIT
Program: WS2812B(neopixel) LED Strip Control Application for Raspberry Pi
Description: This is a simple Python Flask application that controls an addressable RGB LED strip based on API requests.
              The API endpoints are as follows:
              - /set_color: Sets the color of the LED strip
                -> Example request body: {"color": [255, 0, 0]} (for red)
              - /turn_off: Turns off the LED strip
                -> no request body required
              - /rainbow_wave: Starts a rainbow wave effect
                -> no request body required
              - /alternating_colors: Alternates between the specified colors
                -> Example request body: {"color": [255, 0, 0], "color2": [0, 255, 0]} (for red and green)
              - /color_loop: Loops through the specified colors
                -> Example request body: {"colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255]]} (for red, green, and blue)
              - /fade: Fade from bright to dim
                -> Example request body: {"color": [255, 0, 0]}
              - /circle: Circle chasing animation
                -> Example request body: {"color": [255, 0, 0]}
              - /swivel: Back and forth animation
                -> Example request body: {"color": [255, 0, 0]}
              - /random_bright: 80s computer thinking animation
                -> Example request body: {"color": [255, 0, 0], "color2": [0,255,0], "ledsbright": 3}
              - /percent_on: Percentage of leds on, for progress
                -> Example request body: {"color": [255, 0, 0], "percent": 50}
              - /help: Returns documentation of available endpoints and how to use them
Note: 
The standard behavior is that the strip will continue to always display the last color/effect until a new one is set.
There are no time outs, temporary effects, or anything like that. You want it off after a certain amount of time? Send a request to turn it off at that time.
"""

######################################
#              Imports               #
######################################

import spidev
import ws2812
from flask import Flask, request, jsonify
import time
import random
import threading


######################################
#           Configuration            #
######################################

# Define the Flask app
app = Flask(__name__)

# Define the LED strip configuration
# TODO: YOU NEED TO SET THIS TO THE CORRECT NUMBER OF PIXELS IN YOUR STRIP
NUM_LEDS = 24
spi = spidev.SpiDev()
spi.open(1,0)

# Global variables to control animations
current_animation = None
animation_active = False


######################################
#          Helper Functions          #
######################################


# Helper function for the initial flash used at startup to indicate that the program is running
def initial_flash():
    for _ in range(2):  # Flash green three times
        set_color([0,0,31])
        time.sleep(0.3)
        turn_off()
        time.sleep(0.3)
    # Flash blue once
    set_color([31, 0, 0])
    time.sleep(1)
    turn_off()  # light off until told otherwise by API request


######################################
#       LED Control Functions        #
######################################


def set_color(color):
    ws2812.write2812(spi, [color]*NUM_LEDS)


def turn_off():
    ws2812.write2812(spi, [[0,0,0]]*NUM_LEDS)


# This is the rainbow wave effect
def rainbow_cycle(wait):
    global animation_active
    animation_active = True
    l = [[0,0,0]] * NUM_LEDS
    while animation_active:
        for j in range(255):
            for i in range(NUM_LEDS):
                pixel_index = (i * 256 // NUM_LEDS) + j
                color = wheel(pixel_index & 255)
                l[i] = color
            ws2812.write2812(spi, l)
            time.sleep(wait)

def fade(color):
    global animation_active
    animation_active = True
    reverse = False
    steps = 75
    i = 1
    while animation_active:
        l=[[x+i if x>0 else 0 for x in color]]*NUM_LEDS
        ws2812.write2812(spi, l)
        if reverse:
            i -= 1
        else:
            i += 1
        if i == steps:
            reverse = True
        elif i == 0:
            reverse = False
        time.sleep(.01)

def circle(color):
    global animation_active
    animation_active = True
    i = 0
    while animation_active:
        l = [color]*NUM_LEDS
        l[(i+1)%NUM_LEDS] = [x*5 for x in color]
        l[i%NUM_LEDS] = [x*5 for x in color]
        l[(i-1)%NUM_LEDS] = [x*5 for x in color]
        ws2812.write2812(spi, l)
        i += 1
        if i > NUM_LEDS:
            i = 1
        time.sleep(.1)

def swivel(color):
    global animation_active
    animation_active = True
    groups = 3
    i = 0
    rotate = 0
    while animation_active:
        l = [color]*NUM_LEDS
        for n in range(NUM_LEDS):
            if (i+n+rotate) % groups == 0:
                l[n] = [x*5 for x in color]
        ws2812.write2812(spi, l)
        i += 1
        if i >= (NUM_LEDS):
            rotate -= 1
            rotate *= rotate
            i = 0
        time.sleep(0.2)

def random_bright(color, color2, ledsbright=3):
    global animation_active
    animation_active = True
    choice = []
    while animation_active:
        l = [color]*NUM_LEDS
        for i in range(ledsbright):
            r = random.randrange(NUM_LEDS)
            choice.append(r)
        for c in choice:
            l[c] = color2
        ws2812.write2812(spi, l)
        choice = []
        time.sleep(0.13)

def percent_on(color, percent):
    global animation_active
    animation_active = True
    l = [[0,0,0]]*NUM_LEDS
    for i in range(round(NUM_LEDS*(percent/100))):
        l[i] = color
    ws2812.write2812(spi, l)


# Does the alternating colors animation by just calling set_color() with the specified colors
def alternating_colors(color, color2):
    global animation_active
    animation_active = True
    while animation_active:
        set_color(color)
        time.sleep(0.5)
        set_color(color2)
        time.sleep(0.5)


def color_loop(colors):
    global animation_active
    while animation_active:
        for color in colors:
            set_color(color)
            time.sleep(1)


######################################
#     Animation Helper Functions     #
######################################


# Gets called before starting any new animations to stop the current one if one is running
def stop_current_animation():
    global current_animation, animation_active
    animation_active = False
    if current_animation is not None:
        current_animation.join()



# Start the color loop in a separate thread
def start_color_loop(colors):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=color_loop, args=(colors,))
    current_animation.daemon = True
    current_animation.start()

def start_fade(color):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=fade, args=(color,))
    current_animation.daemon = True
    current_animation.start()

def start_circle(color):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=circle, args=(color,))
    current_animation.daemon = True
    current_animation.start()

def start_swivel(color):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=swivel, args=(color,))
    current_animation.daemon = True
    current_animation.start()

def start_random_bright(color, color2, ledsbright):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=random_bright, args=(color, color2, ledsbright,))
    current_animation.daemon = True
    current_animation.start()

def start_percent_on(color, percent):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=percent_on, args=(color, percent,))
    current_animation.daemon = True
    current_animation.start()

# Helper function for the rainbow wave effect, this is used to generate a smooth sequence of color values for the rainbow wave
# This function is taken from the Adafruit example code for the NeoPixel library: https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
# Input a value 0 to 255 to get a color value.
# The colors are a smooth transition of red - green - blue - back to red
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colors are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return [r, g, b]


######################################
#           API Endpoints            #
######################################


@app.route("/set_color", methods=["POST"])
def set_color_endpoint():
    try:
        data = request.get_json()
        color = data["color"]
        stop_current_animation()  # Stop any active animation
        set_color(color)  # Set the new color
        return jsonify({"message": "Color set successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/turn_off", methods=["POST"])
def turn_off_endpoint():
    try:
        stop_current_animation()
        #time.sleep(0.4)
        #turn_off()
        time.sleep(0.1)
        turn_off()  # Doing it again to make sure (sometimes a color stays on)
        time.sleep(0.5)
        return jsonify({"message": "LEDs turned off"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/rainbow_wave", methods=["POST"])
def rainbow_wave_endpoint():
    global current_animation, animation_active
    stop_current_animation()
    animation_active = False  # Stop alternating_colors animation
    time.sleep(0.5)
    current_animation = threading.Thread(target=rainbow_cycle, args=(0.01,))
    current_animation.daemon = True
    current_animation.start()
    return jsonify({"message": "Rainbow wave activated"})


@app.route("/alternating_colors", methods=["POST"])
def alternating_colors_endpoint():
    global current_animation, animation_active
    try:
        data = request.get_json()
        color = data["color"]
        color2 = data["color2"]
        stop_current_animation()  # Stop any active animation
        animation_active = False  # Stop rainbow_wave animation
        current_animation = threading.Thread(
            target=alternating_colors, args=(color, color2)
        )
        current_animation.daemon = True
        current_animation.start()
        return jsonify({"message": "Alternating colors activated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/color_loop", methods=["POST"])
def color_loop_endpoint():
    try:
        data = request.get_json()
        colors = data["colors"]
        start_color_loop(colors)
        return jsonify({"message": "Color loop started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/fade", methods=["POST"])
def fade_endpoint():
    try:
        data = request.get_json()
        color = data["color"]
        start_fade(color,)
        return jsonify({"message": "Fade started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/circle", methods=["POST"])
def circle_endpoint():
    try:
        data = request.get_json()
        color = data["color"]
        start_circle(color)
        return jsonify({"message": "Circle started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/swivel", methods=["POST"])
def swivel_endpoint():
    try:
        data = request.get_json()
        color = data["color"]
        start_swivel(color)
        return jsonify({"message": "Swivel started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/random_bright", methods=["POST"])
def random_bright_endpoint():
    try:
        data = request.get_json()
        color = data["color"]
        color2 = data["color2"]
        ledsbright = int(data["ledsbright"])
        start_random_bright(color, color2, ledsbright)
        return jsonify({"message": "Random Bright started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/percent_on", methods=["POST"])
def percent_on_endpoint():
    try:
        data = request.get_json()
        color = data["color"]
        percent = int(data["percent"])
        start_percent_on(color, percent)
        return jsonify({"message": "Percentage on"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Route for unknown requests
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def unknown_endpoint(path):
    return (
        jsonify(
            {
                "error": "Unknown endpoint or type, use the /help endpoint to get docs of available endpoints"
            }
        ),
        404,
    )


# Route for ping endpoint to check if the server is running
@app.route("/ping")
def ping_endpoint():
    return jsonify({"message": "pong"})


# Route for help endpoint to return documentation of available endpoints and how to use them
@app.route("/help")
def help_endpoint():
    return jsonify(
        {
            "message": "Here's the available endpoints. Note that all requests should be POST requests. All colors should be specified as RGB values, e.g., [255, 0, 0] for red. The controller will always stay displaying the last color/effect until a new one is set.",
            "endpoints": {
                "/set_color": {
                    "description": "Sets the color of the LED strip",
                    "request body": {"color": [255, 0, 0]},  # Red
                },
                "/turn_off": {
                    "description": "Turns off the LED strip",
                    "request body": {},
                },
                "/rainbow_wave": {
                    "description": "Starts a rainbow wave effect",
                    "request body": {},
                },
                "/alternating_colors": {
                    "description": "Alternates between the specified colors",
                    "request body": {
                        "color": [255, 0, 0],  # Red
                        "color2": [0, 255, 0],  # Green
                    },
                },
                "/fade": {
                    "description": "Fade from bright to soft",
                    "request body": {
                        "color": [255, 0, 0],
                    },
                },
                "/circle": {
                    "description": "A chasing circle",
                    "request body": {
                        "color": [255, 0, 0],
                    },
                },
                "/swivel": {
                    "description": "Back and forth animation",
                    "request body": {
                        "color": [255, 0, 0],
                    },
                },
                "/random_bright": {
                    "description": "Randomly brightens leds, like an 80s computer thinking",
                    "request body": {
                        "color": [255, 0, 0],
                        "color2": [0, 255, 0],
                        "ledsbright": 3,
                    },
                },
                "/percent_on": {
                    "description": "Percentage of leds on, for prgress",
                    "request body": {
                        "color": [255, 0, 0],
                        "percent": 50,
                    },
                },
                "/color_loop": {
                    "description": "Loops through the specified colors",
                    "request body": {
                        "colors": [
                            [255, 0, 0],
                            [0, 255, 0],
                            [0, 0, 255],
                        ]  # Red, green, and blue
                    },
                },
                "/help": {
                    "description": "Returns documentation of available endpoints and how to use them (what you are seeing now)",
                    "request body": {},
                },
                "/ping": {
                    "description": 'Returns {"message": "pong"} JSON response to check if the server is running',
                    "request body": {},
                },
            },
        }
    )


######################################
#         Main Entry Point           #
######################################

# The entry point of the program, starts the Flask app and begins listening for endpoint requests
if __name__ == "__main__":
    # Run the initial flash to show we are up and running
    initial_flash()
    # Start the Flask app and begin listening for endpoint requests
    app.run(host="0.0.0.0", port=5060)

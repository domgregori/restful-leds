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
                -> Example request body: {"color1": [255, 0, 0], "color2": [0, 255, 0]} (for red and green)
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
NUM_PIXELS = 20
DATA_PIN = board.D18
pixels = neopixel.NeoPixel(DATA_PIN, NUM_PIXELS, auto_write=False)

# Global variables to control animations
current_animation = None
animation_active = False

# Global variable to store the current brightness
current_brightness = 255  # Default to maximum brightness


######################################
#          Helper Functions          #
######################################


# Helper function for the initial flash used at startup to indicate that the program is running
def initial_flash():
    for _ in range(3):  # Flash green three times
        set_color((0, 255, 0))
        time.sleep(0.5)
        turn_off()
        time.sleep(0.5)
    # Flash blue once
    set_color((0, 0, 255))
    time.sleep(2)
    turn_off()  # light off until told otherwise by API request


######################################
#       LED Control Functions        #
######################################


def set_color(color):
    pixels.fill(color)
    pixels.show()


def turn_off():
    pixels.fill((0, 0, 0))
    pixels.show()


# This is the rainbow wave effect
def rainbow_cycle(wait):
    global animation_active
    animation_active = True
    while animation_active:
        for j in range(255):
            for i in range(NUM_PIXELS):
                pixel_index = (i * 256 // NUM_PIXELS) + j
                color = wheel(pixel_index & 255)
                pixels[i] = color
            pixels.show()
            time.sleep(wait)


# Does the alternating colors animation by just calling set_color() with the specified colors
def alternating_colors(color1, color2):
    global animation_active
    animation_active = True
    while animation_active:
        set_color(color1)
        time.sleep(0.5)
        set_color(color2)
        time.sleep(0.5)


def set_brightness(brightness):
    global current_brightness
    current_brightness = brightness
    pixels.brightness = brightness / 255.0  # Set the brightness between 0 and 1
    pixels.show()


def color_loop(colors):
    global current_brightness, animation_active
    while animation_active:
        for color in colors:
            set_brightness(current_brightness)
            set_color(color)
            time.sleep(1)


def pulse_effect(color):
    global current_brightness, animation_active
    while animation_active:
        for brightness in range(0, 256, 5):
            if not animation_active:
                set_brightness(255)  # Reset brightness to 100%
                return  # Exit the function if animation is stopped
            set_brightness(brightness)
            set_color(color)
            time.sleep(0.1)
        for brightness in range(255, -1, -5):
            if not animation_active:
                set_brightness(255)  # Reset brightness to 100%
                return  # Exit the function if animation is stopped
            set_brightness(brightness)
            set_color(color)
            time.sleep(0.1)
    set_brightness(255)  # Reset brightness to 100% after the pulse effect ends


######################################
#     Animation Helper Functions     #
######################################


# Gets called before starting any new animations to stop the current one if one is running
def stop_current_animation():
    global current_animation, animation_active
    animation_active = False
    if current_animation is not None:
        current_animation.join()


# Start the pulse effect in a separate thread
def start_pulse_effect(color):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=pulse_effect, args=(color,))
    current_animation.daemon = True
    current_animation.start()


# Start the color loop in a separate thread
def start_color_loop(colors):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=color_loop, args=(colors,))
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
    return (r, g, b)


######################################
#           API Endpoints            #
######################################


@app.route("/set_color", methods=["POST"])
def set_color_endpoint():
    try:
        data = request.get_json()
        color = tuple(
            data["color"]
        )  # Color should be a list of RGB values, e.g., [255, 0, 0] for red
        stop_current_animation()  # Stop any active animation
        set_color(color)  # Set the new color
        return jsonify({"message": "Color set successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/turn_off", methods=["POST"])
def turn_off_endpoint():
    try:
        stop_current_animation()
        time.sleep(0.4)
        turn_off()
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
        color1 = tuple(data["color1"])
        color2 = tuple(data["color2"])
        stop_current_animation()  # Stop any active animation
        animation_active = False  # Stop rainbow_wave animation
        current_animation = threading.Thread(
            target=alternating_colors, args=(color1, color2)
        )
        current_animation.daemon = True
        current_animation.start()
        return jsonify({"message": "Alternating colors activated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/set_brightness", methods=["POST"])
def set_brightness_endpoint():
    try:
        data = request.get_json()
        brightness = int(data["brightness"])  # Brightness should be between 0 and 255
        set_brightness(brightness)
        return jsonify({"message": "Brightness set successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/color_loop", methods=["POST"])
def color_loop_endpoint():
    try:
        data = request.get_json()
        colors = [
            tuple(color) for color in data["colors"]
        ]  # List of colors to loop through
        start_color_loop(colors)
        return jsonify({"message": "Color loop started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/pulse_effect", methods=["POST"])
def pulse_effect_endpoint():
    try:
        data = request.get_json()
        color = tuple(
            data["color"]
        )  # Color should be a list of RGB values, e.g., [255, 0, 0] for red
        start_pulse_effect(color)
        return jsonify({"message": "Pulse effect started"})
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
            "message": "Here's the available endpoints. Note that all requests should be POST requests. All colors should be specified as RGB values, e.g., [255, 0, 0] for red. Set brightness values should be between 0 and 255 (like color values). The controller will always stay displaying the last color/effect/brightness until a new one is set.",
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
                        "color1": [255, 0, 0],  # Red
                        "color2": [0, 255, 0],  # Green
                    },
                },
                "/set_brightness": {
                    "description": "Sets the brightness of the LED strip",
                    "request body": {"brightness": 255},  # 100% brightness
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
                "/pulse_effect": {
                    "description": "Starts a pulse effect with the specified color",
                    "request body": {"color": [255, 0, 0]},  # Red
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
    app.run(host="0.0.0.0", port=5000)

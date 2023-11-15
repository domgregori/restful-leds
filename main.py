import board
import neopixel
from flask import Flask, request, jsonify
import time
import colorsys
import threading

app = Flask(__name__)

# Define the LED strip configuration
NUM_PIXELS = 20  # Updated to 20 LEDs
pixels = neopixel.NeoPixel(board.D18, NUM_PIXELS, auto_write=False)

# Variables to control animations
current_animation = None
animation_active = False

# Helper function to stop the current animation
def stop_current_animation():
    global current_animation, animation_active
    animation_active = False
    if current_animation is not None:
        current_animation.join()

# Define a variable to store the current brightness
current_brightness = 255  # Default to maximum brightness

# Helper function for setting brightness
def set_brightness(brightness):
    global current_brightness
    current_brightness = brightness
    pixels.brightness = brightness / 255.0  # Set the brightness between 0 and 1
    pixels.show()

# API endpoint for setting brightness
@app.route('/set_brightness', methods=['POST'])
def set_brightness_endpoint():
    try:
        data = request.get_json()
        brightness = int(data['brightness'])  # Brightness should be between 0 and 255
        set_brightness(brightness)
        return jsonify({"message": "Brightness set successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Helper function for the pulsing effect
def pulse_effect(color):
    global current_brightness

    while animation_active:
        for brightness in range(0, 256, 5):
            if not animation_active:
                return  # Exit the function if animation is stopped
            set_brightness(brightness)
            set_color(color)
            time.sleep(0.1)
        for brightness in range(255, -1, -5):
            if not animation_active:
                return  # Exit the function if animation is stopped
            set_brightness(brightness)
            set_color(color)
            time.sleep(0.1)

# Start the pulse effect in a separate thread
def start_pulse_effect(color):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=pulse_effect, args=(color,))
    current_animation.daemon = True
    current_animation.start()

# API endpoint to start the pulse effect
@app.route('/pulse_effect', methods=['POST'])
def pulse_effect_endpoint():
    try:
        data = request.get_json()
        color = tuple(data['color'])  # Color should be a list of RGB values, e.g., [255, 0, 0] for red
        start_pulse_effect(color)
        return jsonify({"message": "Pulse effect started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Helper function for the color loop
def color_loop(colors):
    global current_brightness

    while animation_active:
        for color in colors:
            set_brightness(current_brightness)
            set_color(color)
            time.sleep(1)

# Start the color loop in a separate thread
def start_color_loop(colors):
    global current_animation, animation_active
    stop_current_animation()
    animation_active = True
    current_animation = threading.Thread(target=color_loop, args=(colors,))
    current_animation.daemon = True
    current_animation.start()

# API endpoint to start the color loop
@app.route('/color_loop', methods=['POST'])
def color_loop_endpoint():
    try:
        data = request.get_json()
        colors = [tuple(color) for color in data['colors']]  # List of colors to loop through

        start_color_loop(colors)
        
        return jsonify({"message": "Color loop started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Define helper functions for controlling the LEDs
def set_color(color):
    pixels.fill(color)
    pixels.show()

def turn_off():
    pixels.fill((0, 0, 0))
    pixels.show()

# Helper function for the initial flash
def initial_flash():
    for _ in range(3):  # Flash green three times
        set_color((0, 255, 0))
        time.sleep(0.5)
        turn_off()
        time.sleep(0.5)
    # Flash blue once
    set_color((0, 0, 255))
    time.sleep(2)
    turn_off()

# Helper function for the rainbow wave effect
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
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

# Helper function for alternating colors
def alternating_colors(color1, color2):
    global animation_active
    animation_active = True

    while animation_active:
        set_color(color1)
        time.sleep(0.5)
        set_color(color2)
        time.sleep(0.5)

# Run the initial flash
initial_flash()

# API endpoints
@app.route('/set_color', methods=['POST'])
def set_color_endpoint():
    try:
        data = request.get_json()
        color = tuple(data['color'])  # Color should be a list of RGB values, e.g., [255, 0, 0] for red
        
        stop_current_animation()  # Stop any active animation
        turn_off()  # Turn off the LEDs to clear them
        set_color(color)  # Set the new color
        
        return jsonify({"message": "Color set successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/turn_off', methods=['POST'])
def turn_off_endpoint():
    try:
        stop_current_animation()
        time.sleep(0.2)
        turn_off()
        time.sleep(0.2)
        turn_off()  # Doing it again to make sure (sometimes a color stays on)
        return jsonify({"message": "LEDs turned off"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/rainbow_wave', methods=['POST'])
def rainbow_wave_endpoint():
    global current_animation, animation_active
    stop_current_animation()
    animation_active = False  # Stop alternating_colors animation

    time.sleep(0.5)
    current_animation = threading.Thread(target=rainbow_cycle, args=(0.01,))
    current_animation.daemon = True
    current_animation.start()
    
    return jsonify({"message": "Rainbow wave activated"})

# Endpoint for alternating colors
@app.route('/alternating_colors', methods=['POST'])
def alternating_colors_endpoint():
    try:
        data = request.get_json()
        color1 = tuple(data['color1'])
        color2 = tuple(data['color2'])

        stop_current_animation()  # Stop any active animation
        animation_active = False  # Stop rainbow_wave animation

        current_animation = threading.Thread(target=alternating_colors, args=(color1, color2))
        current_animation.daemon = True
        current_animation.start()
        
        return jsonify({"message": "Alternating colors activated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

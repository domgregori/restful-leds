# Pi LED Controller Web API

This is a Python program for the Raspberry Pi that allows you to control a strip of WS2812B (NeoPixel) addressable LEDs using a REST API. Any Raspberry Pi model will work, I like to use the Pi Zero W because it's cheap, small, and has built-in WiFi. The processing requirements for this program are very low, so even the weak Pi Zero W can handle it just fine, but installing things will take a little more patience :)

## Installation

Follow these steps to install the necessary packages and libraries:

```bash
sudo apt update
sudo apt upgrade
sudo apt install python3-pip git
sudo pip3 install flask adafruit-circuitpython-neopixel
```

Clone the repository to your Raspberry Pi:

```bash
git clone https://github.com/EthyMoney/pi-neopixel-http-api-controller.git
```

## Configuration

You need to open the `main.py` file and set the `NUM_PIXELS` variable to the count of leds in your strip. You can also change the GPIO pin that the data pin of the strip is connected to by changing the `DATA_PIN` variable. This needs to be a PWM-capable pin like GPIO 12, GPIO 13, GPIO 18, GPIO 19. The default is GPIO pin 18, which is represented in the code as `board.D18`. You can find a list of GPIO pin numbers [here](https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header).

## Hardware Setup

Connect the data pin of the LED strip to GPIO pin 18 on the Raspberry Pi (default), or whatever you changed it to. Connect the ground pin of the LED strip to any ground pin on the Raspberry Pi **AND** the ground of the power supply. Yes, the strip should have a common ground with the Pi and power supply, you will have issues if you don't do this. Connect the power pin of the LED strip to a power supply of correct voltage for your strip, this is typically either 5v, 12v or 24v. Make sure your power supply has enough current to power your strip. Assuming 12v, you typically need 1 amp per meter of strip as a very general rule of thumb. For example, a 5 meter 12v strip would need a 5 amp 12v power supply.

## Running the Program

You can run the program directly with Python:
  
```bash
sudo python3 main.py
```

## Running with PM2 (Recommended)

PM2 is a process manager for Node.js applications. The repository includes a PM2 process definition json file, which allows you to run the app as a background process and automatically start it on boot.

First, edit the `process.json` file to replace the path to the `main.py` file with the path to your copy of the repository on your pi.

Then, install PM2:

```bash
sudo apt update && sudo apt install npm -y && sudo npm install pm2 -g
```

Now, start the app with PM2, save the process list, and set to start on boot:

```bash
sudo pm2 start process.json
sudo pm2 save
sudo pm2 startup
```

## API Endpoints

The program runs a web server on port 5000 hosting a REST API and set of endpoints for controlling the connected LED strip. The base API URL is `http://<your-pi-ip-address>:5000/`. Here are the available endpoints:

- `/set_color`: Sets the color of the LED strip.
  - Method: `POST`
  - Request body: `{"color": [255, 0, 0]}` (for red)

- `/turn_off`: Turns off the LED strip.
  - Method: `POST`
  - Request body: None

- `/rainbow_wave`: Starts a rainbow wave effect.
  - Method: `POST`
  - Request body: None

- `/alternating_colors`: Alternates between the specified colors.
  - Method: `POST`
  - Request body: `{"color1": [255, 0, 0], "color2": [0, 255, 0]}` (for red and green)

- `/set_brightness`: Sets the brightness of the LED strip.
  - Method: `POST`
  - Request body: `{"brightness": 100}` (for 100% brightness)

- `/color_loop`: Loops through the specified colors.
  - Method: `POST`
  - Request body: `{"colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255]]}` (for red, green, and blue)

- `/pulse_effect`: Starts a pulse effect with the specified color.
  - Method: `POST`
  - Request body: `{"color": [255, 0, 0]}` (for red)

- `/help`: Returns a list of available endpoints and their usage (basically what you are looking at right now)
  - Method: `GET`
  - Request body: None

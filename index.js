const ws281x = require('rpi-ws281x-native');

const NUM_LEDS = 20;     // Number of LEDs
const GPIO_PIN = 18;     // GPIO pin
const waveLength = 3;    // Number of LEDs per color wave
const delayTime = 50;    // Delay time in ms

console.log('Starting LED strip...');

ws281x.init(NUM_LEDS, { gpioPin: GPIO_PIN });

// Set the entire strip to a single color
function setColor(color) {
  const colors = [];

  for (let i = 0; i < NUM_LEDS; i++) {
    colors.push(color);
  }

  ws281x.render(colors);
}

console.log('Setting to red...');

// Set the entire strip to a single color
setColor(rgb2Int(255, 0, 0)); // Red

console.log("Done!")

// keep the program running
process.stdin.resume(); //so the program will not close instantly



// Define a function to convert RGB to a single integer value
function rgb2Int(r, g, b) {
  return ((r << 16) | (g << 8) | b);
}

// Create a rainbow wave pattern
function rainbowWave() {
  let offset = 0;

  return function () {
    const colors = [];

    for (let i = 0; i < NUM_LEDS; i++) {
      const hue = ((i * waveLength) + offset) % 360;
      colors.push(hsvToRgb(hue, 1, 1));
    }

    offset = (offset + 1) % 360;
    return colors;
  };
}

// Convert HSV to RGB
function hsvToRgb(h, s, v) {
  let r, g, b, i, f, p, q, t;
  i = Math.floor(h * 6);
  f = h * 6 - i;
  p = v * (1 - s);
  q = v * (1 - f * s);
  t = v * (1 - (1 - f) * s);

  switch (i % 6) {
    case 0: r = v, g = t, b = p; break;
    case 1: r = q, g = v, b = p; break;
    case 2: r = p, g = v, b = t; break;
    case 3: r = p, g = q, b = v; break;
    case 4: r = t, g = p, b = v; break;
    case 5: r = v, g = p, b = q; break;
  }

  return rgb2Int(Math.round(r * 255), Math.round(g * 255), Math.round(b * 255));
}

// const wave = rainbowWave();

// // Render loop
// function render() {
//   ws281x.render(wave().map(hsvToRgb));
//   setTimeout(render, delayTime);
// }

// // Start the loop
// render();

// Ensure LEDs are turned off on exit
process.on('SIGINT', function () {
  ws281x.reset();
  process.nextTick(function () { process.exit(0); });
});

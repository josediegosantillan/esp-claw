local ls    = require("led_strip")
local delay = require("delay")

-- Update these values to match the LED strip wiring on the target board.
local LED_GPIO_NUM = 26
local LED_COUNT = 16

-- Create the strip handle and drive all pixels together.
print("[led] creating led strip on gpio " .. tostring(LED_GPIO_NUM))
local strip, serr = ls.new(LED_GPIO_NUM, LED_COUNT)
if not strip then
    print("[led] ERROR: failed to create led strip: " .. tostring(serr))
    return
end
print("[led] led strip created")

-- Clear first so the demo always starts from a known LED state.
strip:clear()
print("[led] strip cleared")

local function fill_all_rgb(r, g, b)
    for index = 0, LED_COUNT - 1 do
        strip:set_pixel(index, r, g, b)
    end
end

local function draw_rainbow(offset)
    for index = 0, LED_COUNT - 1 do
        local hue = ((index * 360) // LED_COUNT + offset) % 360
        strip:set_pixel_hsv(index, hue, 255, 64)
    end
end

print("[led] flash start")
for i = 1, 3 do
    fill_all_rgb(255, 255, 255)
    strip:refresh()
    delay.delay_ms(150)

    strip:clear()
    strip:refresh()
    delay.delay_ms(150)
end
print("[led] flash end")

print("[led] rainbow animation start")
for offset = 0, 720, 8 do
    draw_rainbow(offset)
    strip:refresh()
    delay.delay_ms(40)
end

print("[led] rainbow animation end")
strip:clear()
strip:refresh()
print("[led] done")

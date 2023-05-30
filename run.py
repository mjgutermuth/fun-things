import statistics
import colorsys

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_grayscale_level(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    grayscale_level = 1 - statistics.stdev([r, g, b]) / 127.5
    return grayscale_level

def get_brightness_description(hex_color):
    if get_grayscale_level(hex_color) > 0.5:
        return "muted"
    else:
        return "bright"

def get_color_description(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    r, g, b = [x/255.0 for x in (r, g, b)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    descriptions = []

    if l < 0.33:
        descriptions.append("dark")
    elif l < 0.66:
        descriptions.append("medium")
    else:
        descriptions.append("light")

    if is_muted(hex_color):
        descriptions.append("muted")
    else:
        descriptions.append("bright")

    if (r + g) > 2 * b:  # sum of red and green is dominant over twice the blue component
        descriptions.append("with warm undertones")
    else:
        descriptions.append("with cool undertones")

    return " ".join(descriptions)

hex_color = input("Enter a hex color: ")
print("Color Description:", get_color_description(hex_color))
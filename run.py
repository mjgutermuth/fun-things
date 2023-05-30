import statistics
import colorsys

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_grayscale_level(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return 1 - statistics.stdev([r, g, b]) / 127.5

def is_muted(hex_color):
    return get_grayscale_level(hex_color) > 0.5

def is_bright(hex_color):
    return not is_muted(hex_color)

def get_color_description(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    r, g, b = [x/255.0 for x in (r, g, b)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    descriptions = []
    if l < 0.5:
        descriptions.append("dark")
    else:
        descriptions.append("light")

    if is_muted(hex_color):
        descriptions.append("muted")
    else:
        descriptions.append("vivid")

    if 0 <= h < 1/6:
        descriptions.append("with red tones")
    elif 1/6 <= h < 1/3:
        descriptions.append("with yellow tones")
    elif 1/3 <= h < 1/2:
        descriptions.append("with green tones")
    elif 1/2 <= h < 2/3:
        descriptions.append("with cyan tones")
    elif 2/3 <= h < 5/6:
        descriptions.append("with blue tones")
    else:
        descriptions.append("with magenta tones")

    return " ".join(descriptions)

hex_color = input("Enter a hex color: ")
print("Grayscale Level:", get_grayscale_level(hex_color))
print("Is Muted:", is_muted(hex_color))
print("Is Bright:", is_bright(hex_color))
print("Color Description:", get_color_description(hex_color))


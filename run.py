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

    if r > (g + b) / 2:  # red is dominant
        if b > 0.25 * (r + b):  # blue component is more than 25% of the red-blue sum
            descriptions.append("with cool undertones")
        else:
            descriptions.append("with warm undertones")
    else:
        if b > 0.4 or g > 0.6:  # Adjusted the blue threshold down and added a green threshold
            descriptions.append("with cool undertones")
        else:
            descriptions.append("with warm undertones")

    return " ".join(descriptions)

hex_color = input("Enter a hex color: ")
print("Grayscale Level:", get_grayscale_level(hex_color))
print("Is Muted:", is_muted(hex_color))
print("Is Bright:", is_bright(hex_color))
print("Color Description:", get_color_description(hex_color))
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

    h *= 360  # convert hue to degrees for easier interpretation

    # Color-specific undertone rules
    if 0 <= h < 30:  # reds
        color_name = "red"
        if b > 0.25 * (r + b):
            descriptions.append("with cool undertones")
        else:
            descriptions.append("with warm undertones")
    elif 30 <= h < 90:  # yellows and oranges
        color_name = "yellow"
        if b > 0:
          descriptions.append("with cool undertones")
        else:
          descriptions.append("with warm undertones")
    elif 90 <= h < 150:  # greens
        color_name = "green"
        if r > 0.33 * (g + b):
            descriptions.append("with warm undertones")
        else:
            descriptions.append("with cool undertones")
    elif 150 <= h < 210:  # cyans
        color_name = "cyan"
        if r > 0.2 * (g + b):
            descriptions.append("with warm undertones")
        else:
            descriptions.append("with cool undertones")
    elif 210 <= h < 270:  # blues
        color_name = "blue"
        if r > 0.2 * (g + b):
            descriptions.append("with warm undertones")
        else:
            descriptions.append("with cool undertones")
    elif 270 <= h < 330:  # purples
        color_name = "purple"
        if r < b:
            descriptions.append("with cool undertones")
        else:
            descriptions.append("with warm undertones")
    else:  # pinks and reds
        color_name = "pink"
        if b > 0.33 * (r + b):
            descriptions.append("with cool undertones")
        else:
            descriptions.append("with warm undertones")

    # add the color name to the description
    descriptions.insert(2, color_name)

    return " ".join(descriptions)

hex_color = input("Enter a hex color: ")
print("Color Description:", get_color_description(hex_color))
function getColorNameByHex(hexColor) {
    const hex = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
    const apiUrl = `https://www.thecolorapi.com/id?hex=${hex}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const colorName = data.name.value;
            const colorDescription = getColorDescription(hexColor, colorName);
            document.getElementById('colorInfoDisplay').innerText = colorDescription;

            // Change background color directly
            document.body.style.backgroundColor = hexColor;
            // Change text color based on brightness of hex color
            document.body.style.color = chroma.contrast(hexColor, 'white') > 4.5 ? 'white' : 'black';
        })
        .catch(error => console.error('Error fetching color name:', error));
}

function isLight(hexColor) {
    // Convert hex color to RGB
    let { r, g, b } = hexToRgb(hexColor);

    // Calculate perceived brightness using YIQ color space
    let brightness = (r * 299 + g * 587 + b * 114) / 1000;

    // Return true if brightness is greater than 128, indicating a light color
    return brightness > 128;
}

function hexToRgb(hex) {
    // Convert hex color to RGB
    let bigint = parseInt(hex.replace('#', ''), 16);
    let r = (bigint >> 16) & 255;
    let g = (bigint >> 8) & 255;
    let b = bigint & 255;

    return { r, g, b };
}

function deriveColorName(h, s, l) {
    if (l < 0.1) return "black";
    if (l > 0.9) return "white";
    if (s < 0.15 && l >= 0.1 && l < 0.7) {
        return "gray";
    }

    if ((h >= 0 && h < 20) || (h >= 350 && h <= 360)) return "red";
    if (h >= 20 && h < 47) return "orange";
    if (h >= 47 && h < 82) return "yellow";
    if (h >= 82 && h < 178) return "green";
    if (h >= 178 && h < 183) return "teal";
    if (h >= 183 && h < 260) return "blue";
    if (h >= 260 && h < 308) return "purple";
    if (h >= 308 && h < 332) return "pink";

    if (l < 0.55 && (s >= 0.3 && s < 0.8) && (h >= 47 && h < 82)) return "brown";

    return "color"; // A fallback for colors not fitting into the above categories.
}

function determineUndertone(h, s, l) {
    // Basic undertone determination based on hue
    let undertone = 'neutral'; // Default to neutral for low saturation or extreme lightness/darkness

    if (s > 0.2 && !(l > 0.8 || l < 0.2)) {
        if ((h >= 0 && h < 30) || (h >= 330 && h <= 360)) {
            // Red: warmer if closer to orange, cooler if closer to pink
            undertone = h < 15 || h > 345 ? 'warm' : 'cool';
        } else if (h >= 30 && h < 90) {
            // Orange to Yellow: generally warm
            undertone = 'warm';
        } else if (h >= 90 && h < 150) {
            // Green: cooler if more blueish, warmer if more yellowish
            undertone = h < 120 ? 'warm' : 'cool';
        } else if (h >= 150 && h < 210) {
            // Cyan to Light Blue: generally cool
            undertone = 'cool';
        } else if (h >= 210 && h < 270) {
            // Blue: cooler, especially at higher saturations
            undertone = 'cool';
        } else if (h >= 270 && h < 330) {
            // Purple to Pink: cooler if more blueish, warmer if closer to red
            undertone = h < 300 ? 'cool' : 'warm';
        }
    }

    return undertone;
}

function getColorDescription(hexColor, colorName) {
    const color = chroma(hexColor);
    const [h, s, l] = color.hsl();
    let descriptiveColorName = deriveColorName(h, s, l);
    let lightnessDesc = l < 0.33 ? "dark" : l <= 0.66 ? "medium" : "light";
    let brightnessDesc = s < 0.8 ? "muted" : "bright";
    let undertoneDesc = determineUndertone(h, s, l);

    // Incorporate the fetched color name into the description
    let descriptionParts = [`${colorName}: a ${lightnessDesc}, ${brightnessDesc} ${descriptiveColorName} with ${undertoneDesc} undertones`];
    return descriptionParts.join(" ");
}

function displayColorDescription() {
    let hexColor = document.getElementById('hexColorInput').value;
    getColorNameByHex(hexColor);
}
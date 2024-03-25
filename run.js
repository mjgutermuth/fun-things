function getColorNameByHex(hexColor) {
    const hex = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
    const apiUrl = `https://www.thecolorapi.com/id?hex=${hex}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const colorName = data.name.value;
            const colorDescription = getColorDescription(hexColor, colorName);
            document.getElementById('colorInfoDisplay').innerText = colorDescription;

        })
        .catch(error => console.error('Error fetching color name:', error));
}

function deriveColorName(h, s, l) {
    if (l < 0.1) return "black";
    if (l > 0.9) return "white";

    // Adjusted conditions for brown
    if (((h >= 10 && h <= 40) || (h > 340 && h < 30)) && (s >= 0.3 && s < 0.8) && (l >= 0.2 && l < 0.6)) {
        return "brown";
    }

    // Adjusted conditions for gray
    if (s < 0.15 && l >= 0.1 && l < 0.7) {
        return "gray";
    }

    if ((h >= 0 && h < 30) || (h >= 330 && h <= 360)) return "red";
    if (h >= 30 && h < 45) return "orange";
    if (h >= 45 && h < 75) return "yellow";
    if (h >= 75 && h < 165) return "green";
    if (h >= 165 && h < 195) return "teal";
    if (h >= 195 && h < 225) return "blue";
    if (h >= 225 && h < 275) return "indigo";
    if (h >= 275 && h < 330) return "purple";
    
    return "color"; // A more descriptive fallback for colors not fitting into the above categories.
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

    let lightnessDesc = l < 0.33 ? "dark" : l <= 0.66 ? "medium" : "light";
    let brightnessDesc = s < 0.33 ? "muted" : "bright";
    let descriptiveColorName = deriveColorName(h, s, l);
    let undertoneDesc = determineUndertone(h, s, l);

    // Incorporate the fetched color name into the description
    let descriptionParts = [`${colorName}: a ${lightnessDesc}, ${brightnessDesc} ${descriptiveColorName} with ${undertoneDesc} undertones`];
    return descriptionParts.join(" ");
}


function displayColorDescription() {
    let hexColor = document.getElementById('hexColorInput').value;
    getColorNameByHex(hexColor);
}

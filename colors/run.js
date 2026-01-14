function getColorNameByHex(hexColor) {
    const hex = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
    const apiUrl = `https://www.thecolorapi.com/id?hex=${hex}`;

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Color API request failed');
            }
            return response.json();
        })
        .then(data => {
            const colorName = data.name.value;
            const colorDescription = getColorDescription(hexColor, colorName);
            document.getElementById('colorInfoDisplay').innerText = colorDescription;

            // Change background color directly
            document.body.style.backgroundColor = hexColor;
            // Change text color based on brightness of hex color
            document.body.style.color = chroma.contrast(hexColor, 'white') > 4.5 ? 'white' : 'black';
        })
        .catch(() => {
            document.getElementById('colorInfoDisplay').innerText = 'Error: Could not fetch color information. Please try again.';
        });
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
    let derivedColor = "";

    if (l < 0.1) {
        derivedColor = "black";
    } else if (l > 0.9) {
        derivedColor = "white";
    } else if (s < 0.15 && l >= 0.1 && l <= 0.9) {
        derivedColor = "gray";
    } else {
        if (h >= 0 && h < 20) {
            derivedColor = "red";
        } else if (h >= 20 && h < 47) {
            derivedColor = "orange";
        } else if (h >= 47 && h < 65) {
            derivedColor = "yellow";
        } else if (h >= 65 && h < 82) {
            derivedColor = "lime";
        } else if (h >= 82 && h < 165) {
            derivedColor = "green";
        } else if (h >= 165 && h < 185) {
            derivedColor = "teal";
        } else if (h >= 185 && h < 240) {
            derivedColor = "blue";
        } else if (h >= 240 && h < 300) {
            derivedColor = "purple";
        } else if (h >= 300 && h < 330) {
            derivedColor = "pink";
        } else {
            derivedColor = "red";
        }
    }

    return derivedColor;
}

function determineUndertone(r, g, b, derivedColor) {
    // Define undertone rules based on the derived color name
    const undertoneRules = {
        "red": (g > b) ? "warm" : "cool",
        "orange": "warm",
        "yellow": (b >= 0.4 * g) ? "cool" : "warm",
        "green": (b > r && b > g) ? "cool" : "warm",
        "teal": (g > 1.3 * b) ? "warm" : "cool",
        "blue": (r >= 0.4 * b) ? "warm" : "cool",
        "purple": (b > r) ? "cool" : "warm",
        "pink": (b > r) ? "cool" : "warm",
        "brown": (r > g && r > b) ? "warm" : "cool",
        "white": (r > 230 && g > 230 && b > 230) ?
                  ((r > g && r > b) ? "warm" :
                  (b > r && b > g) ? "cool" :
                  (Math.abs(r - g) < 10 && Math.abs(g - b) < 10 && Math.abs(r - b) < 10) ? "neutral" :
                  "warm") : "neutral" // Warm if red is dominant, cool if blue is dominant, neutral otherwise
    };

    if (undertoneRules.hasOwnProperty(derivedColor)) {
        return undertoneRules[derivedColor];
    } else {
        return "neutral";
    }
}

function getColorDescription(hexColor, colorName) {
    const color = chroma(hexColor);
    const [h, s, l] = color.hsl();
    const { r, g, b } = hexToRgb(hexColor);
    const derivedColor = deriveColorName(h, s, l);

    let lightnessDesc = l < 0.33 ? "dark" : l <= 0.66 ? "medium" : "light";
    let brightnessDesc = s < 0.8 ? "muted" : "bright";

    let undertoneDesc = determineUndertone(r, g, b, derivedColor);

    // Incorporate the fetched color name into the description
    let descriptionParts = [`${colorName}: a ${lightnessDesc}, ${brightnessDesc} ${derivedColor} with ${undertoneDesc} undertones`];
    return descriptionParts.join(" ");
}


function isValidHex(hex) {
    const cleanHex = hex.startsWith('#') ? hex.slice(1) : hex;
    return /^[0-9A-Fa-f]{6}$|^[0-9A-Fa-f]{3}$/.test(cleanHex);
}

function displayColorDescription() {
    let hexColor = document.getElementById('hexColorInput').value.trim();
    if (!hexColor) {
        document.getElementById('colorInfoDisplay').innerText = 'Please enter a hex color.';
        return;
    }
    if (!hexColor.startsWith('#')) {
        hexColor = `#${hexColor}`;
    }
    if (!isValidHex(hexColor)) {
        document.getElementById('colorInfoDisplay').innerText = 'Invalid hex color. Please enter a valid hex (e.g., #FF5733 or FF5733).';
        return;
    }
    getColorNameByHex(hexColor);
}

document.addEventListener('DOMContentLoaded', () => {
    const hexInput = document.getElementById('hexColorInput');
    const colorPicker = document.getElementById('colorPicker');

    hexInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            displayColorDescription();
        }
    });

    colorPicker.addEventListener('input', (e) => {
        hexInput.value = e.target.value;
        displayColorDescription();
    });
});
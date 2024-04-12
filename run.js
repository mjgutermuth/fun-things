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
    let derivedColor = "";

    if (l < 0.1) {
        derivedColor = "black";
    } else if (l > 0.9) {
        derivedColor = "white";
    } else if (s < 0.15 && l >= 0.1 && l < 0.7) {
        derivedColor = "gray";
    } else if ((h >= 0 && h < 20) || (h >= 350 && h <= 360)) {
        derivedColor = "red";
    } else if (h >= 20 && h < 47) {
        derivedColor = "orange";
    } else if (h >= 47 && h < 82) {
        derivedColor = "yellow";
    } else if (h >= 82 && h < 178) {
        derivedColor = "green";
    } else if (h >= 178 && h < 183) {
        derivedColor = "teal";
    } else if (h >= 183 && h < 260) {
        derivedColor = "blue";
    } else if (h >= 260 && h < 308) {
        derivedColor = "purple";
    } else if (h >= 308 && h < 332) {
        derivedColor = "pink";
    } else if (l < 0.55 && (s >= 0.3 && s < 0.8) && (h >= 47 && h < 82)) {
        derivedColor = "brown";
    } else {
        derivedColor = "color"; // A fallback for colors not fitting into the above categories.
    }

    console.log("Derived color:", derivedColor); // Log the derived color before returning it

    return derivedColor;
}

function determineUndertone(r, g, b, derivedColor) {
    console.log("Input RGB values:", r, g, b);

    // Define undertone rules based on the derived color name
    const undertoneRules = {
        "red": (g > b) ? "warm" : "neutral",
        "orange": (r > g && g > b) ? "warm" : "neutral",
        "yellow": (r > b && g > b) ? "warm" : "neutral",
        "green": (b > r && b > g) ? "cool" : "neutral",
        "teal": (b > r && b > g) ? "cool" : "neutral",
        "blue": (b > r && b > g) ? "cool" : "neutral",
        "indigo": (b > r && b > g) ? "cool" : "neutral",
        "purple": (b > r && b > g) ? "cool" : "neutral",
        "pink": (b > r && b > g) ? "cool" : "neutral",
        "brown": (r > g && r > b) ? "warm" : "neutral",
    };

    // Check if the derived color has a specific undertone rule
    if (undertoneRules.hasOwnProperty(derivedColor)) {
        const undertone = undertoneRules[derivedColor];
        console.log("Undertone:", undertone);
        return undertone;
    } else {
        // Default to neutral if no specific undertone rule is defined
        console.log("Undertone: undefined");
        return "neutral";
    }
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
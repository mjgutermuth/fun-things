// Constants
const CONTRAST_RATIO_THRESHOLD = 4.5;
const API_TIMEOUT_MS = 5000;
const DEBOUNCE_DELAY_MS = 300;

// Lightness thresholds for color naming
const LIGHTNESS_BLACK_THRESHOLD = 0.07;
const LIGHTNESS_WHITE_THRESHOLD = 0.97;
const SATURATION_GRAY_THRESHOLD = 0.15;
const LIGHTNESS_BROWN_MAX = 0.35;
const SATURATION_BROWN_MAX = 0.55;

// RGB thresholds for white detection
const RGB_WHITE_MIN = 230;
const RGB_NEUTRAL_TOLERANCE = 10;

// Track the latest request to prevent race conditions
let latestRequestId = 0;

function fetchWithTimeout(url, timeoutMs) {
    return Promise.race([
        fetch(url),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timed out')), timeoutMs)
        )
    ]);
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function setLoadingState(isLoading) {
    const display = document.getElementById('colorInfoDisplay');
    const button = document.querySelector('button');
    if (isLoading) {
        display.innerText = 'Loading...';
        button.disabled = true;
    } else {
        button.disabled = false;
    }
}

function showError(message, hexColor) {
    const display = document.getElementById('colorInfoDisplay');
    const retryButton = document.createElement('button');
    retryButton.innerText = 'Retry';
    retryButton.className = 'retry-button';
    retryButton.onclick = () => getColorNameByHex(hexColor);

    display.innerText = message + ' ';
    display.appendChild(retryButton);
}

function getColorNameByHex(hexColor) {
    const hex = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
    const apiUrl = `https://www.thecolorapi.com/id?hex=${hex}`;

    const requestId = ++latestRequestId;
    setLoadingState(true);

    fetchWithTimeout(apiUrl, API_TIMEOUT_MS)
        .then(response => {
            if (!response.ok) {
                throw new Error('Color API request failed');
            }
            return response.json();
        })
        .then(data => {
            // Ignore if a newer request has been made
            if (requestId !== latestRequestId) return;

            const colorName = data.name.value;
            const colorDescription = getColorDescription(hexColor, colorName);
            document.getElementById('colorInfoDisplay').innerText = colorDescription;

            // Change background color directly
            document.body.style.backgroundColor = hexColor;
            // Change text color based on brightness of hex color
            document.body.style.color = chroma.contrast(hexColor, 'white') > CONTRAST_RATIO_THRESHOLD ? 'white' : 'black';
        })
        .catch((error) => {
            // Ignore if a newer request has been made
            if (requestId !== latestRequestId) return;

            // Use fallback color naming
            const fallbackDescription = getColorDescriptionFallback(hexColor);
            if (fallbackDescription) {
                document.getElementById('colorInfoDisplay').innerText = fallbackDescription + ' (offline)';
                document.body.style.backgroundColor = hexColor;
                document.body.style.color = chroma.contrast(hexColor, 'white') > CONTRAST_RATIO_THRESHOLD ? 'white' : 'black';
            } else {
                const message = error.message === 'Request timed out'
                    ? 'Error: Request timed out.'
                    : 'Error: Could not fetch color information.';
                showError(message, hexColor);
            }
        })
        .finally(() => {
            if (requestId === latestRequestId) {
                setLoadingState(false);
            }
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

    if (l < LIGHTNESS_BLACK_THRESHOLD) {
        derivedColor = "black";
    } else if (l > LIGHTNESS_WHITE_THRESHOLD) {
        derivedColor = "white";
    } else if (s < SATURATION_GRAY_THRESHOLD) {
        derivedColor = "gray";
    } else {
        // Check for brown: dark to medium-dark, not too saturated, in the red/orange/yellow hue range
        if (l < LIGHTNESS_BROWN_MAX && s < SATURATION_BROWN_MAX && ((h >= 0 && h < 50) || h >= 350)) {
            derivedColor = "brown";
        } else if (h >= 0 && h < 20) {
            derivedColor = "red";
        } else if (h >= 20 && h < 47) {
            derivedColor = "orange";
        } else if (h >= 47 && h < 65) {
            derivedColor = "yellow";
        } else if (h >= 65 && h < 165) {
            derivedColor = "green";
        } else if (h >= 165 && h < 185) {
            derivedColor = "teal";
        } else if (h >= 185 && h < 240) {
            derivedColor = "blue";
        } else if (h >= 240 && h < 300) {
            derivedColor = "purple";
        } else if (h >= 300 && h < 350) {
            derivedColor = "pink";
        } else {
            derivedColor = "red";
        }
    }

    return derivedColor;
}

function determineUndertone(r, g, b, derivedColor) {
    // Normalize RGB values from 0-255 to 0-1 range for consistent comparisons
    const rNorm = r / 255;
    const gNorm = g / 255;
    const bNorm = b / 255;

    // Define undertone rules based on the derived color name
    // Using normalized values (0-1) for ratio comparisons
    const undertoneRules = {
        "red": (gNorm > bNorm) ? "warm" : "cool",
        "orange": "warm",
        "yellow": (bNorm >= 0.4 * gNorm) ? "cool" : "warm",
        "green": (bNorm > 0.4 * gNorm) ? "cool" : "warm",
        "teal": (gNorm > 1.3 * bNorm) ? "warm" : "cool",
        "blue": (rNorm >= 0.6 * bNorm) ? "warm" : "cool",
        "purple": (bNorm > rNorm) ? "cool" : "warm",
        "pink": (bNorm > 0.6 * rNorm) ? "cool" : "warm",
        "brown": (rNorm > gNorm && rNorm > bNorm) ? "warm" : "cool",
        "white": (r > RGB_WHITE_MIN && g > RGB_WHITE_MIN && b > RGB_WHITE_MIN) ?
                  ((r > g && r > b) ? "warm" :
                  (b > r && b > g) ? "cool" :
                  (Math.abs(r - g) < RGB_NEUTRAL_TOLERANCE && Math.abs(g - b) < RGB_NEUTRAL_TOLERANCE && Math.abs(r - b) < RGB_NEUTRAL_TOLERANCE) ? "neutral" :
                  "warm") : "neutral"
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

function getColorDescriptionFallback(hexColor) {
    try {
        const color = chroma(hexColor);
        const [h, s, l] = color.hsl();
        const { r, g, b } = hexToRgb(hexColor);
        const derivedColor = deriveColorName(h, s, l);

        let lightnessDesc = l < 0.33 ? "dark" : l <= 0.66 ? "medium" : "light";
        let brightnessDesc = s < 0.8 ? "muted" : "bright";
        let undertoneDesc = determineUndertone(r, g, b, derivedColor);

        // Capitalize derived color name as fallback
        const colorName = derivedColor.charAt(0).toUpperCase() + derivedColor.slice(1);
        return `${colorName}: a ${lightnessDesc}, ${brightnessDesc} ${derivedColor} with ${undertoneDesc} undertones`;
    } catch {
        return null;
    }
}


function isValidHex(hex) {
    const cleanHex = hex.startsWith('#') ? hex.slice(1) : hex;
    return /^[0-9A-Fa-f]{6}$|^[0-9A-Fa-f]{3}$/.test(cleanHex);
}

function expandHex(hex) {
    // Expand 3-digit hex to 6-digit (e.g., #FFF -> #FFFFFF)
    const cleanHex = hex.startsWith('#') ? hex.slice(1) : hex;
    if (cleanHex.length === 3) {
        const expanded = cleanHex.split('').map(c => c + c).join('');
        return '#' + expanded;
    }
    return hex.startsWith('#') ? hex : '#' + hex;
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
    // Expand 3-digit hex to 6-digit for API compatibility
    hexColor = expandHex(hexColor);
    getColorNameByHex(hexColor);
}

// Debounced version for color picker
const debouncedDisplayColorDescription = debounce(displayColorDescription, DEBOUNCE_DELAY_MS);

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
        debouncedDisplayColorDescription();
    });
});
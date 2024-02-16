async function fetchColorInfo(hexColor) {
    const apiUrl = `https://api.example.com/color?hex=${hexColor}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        const colorInfo = await response.json();
        return colorInfo;
    } catch (error) {
        console.error('Error fetching color info:', error);
    }
}

function hexToRgb(hexColor) {
    let r = parseInt(hexColor.slice(1, 3), 16);
    let g = parseInt(hexColor.slice(3, 5), 16);
    let b = parseInt(hexColor.slice(5, 7), 16);
    return [r, g, b];
}

function getGrayscaleLevel(hexColor) {
    let [r, g, b] = hexToRgb(hexColor);
    let mean = (r + g + b) / 3;
    let stdev = Math.sqrt(((r - mean) ** 2 + (g - mean) ** 2 + (b - mean) ** 2) / 3);
    return 1 - stdev / 127.5;
}

function getBrightnessDescription(hexColor) {
    return getGrayscaleLevel(hexColor) > 0.5 ? "muted" : "bright";
}

function rgbToHls(r, g, b) {
    r /= 255, g /= 255, b /= 255;
    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, l = (max + min) / 2, s = 0;

    if (max !== min) {
        let d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }

    return [h * 360, l, s];
}

function getColorDescription(hexColor) {
    let [r, g, b] = hexToRgb(hexColor);
    let [h, l, s] = rgbToHls(r, g, b);

    let descriptions = [];
    let colorName = "";

    // Check lightness level
    if (l < 0.33) {
        descriptions.push("dark");
    } else if (l < 0.66) {
        descriptions.push("medium");
    } else {
        descriptions.push("light");
    }

    // Check brightness level
    if (getBrightnessDescription(hexColor) === "muted") {
        descriptions.push("muted");
    } else {
        descriptions.push("bright");
    }

    // Convert hue to degrees for easier interpretation
    h *= 360;

    // Color-specific undertone rules
    if (0 <= h && h < 30) {  // reds
        colorName = "red";
        descriptions.push(b > 0.25 * (r + b) ? "with cool undertones" : "with warm undertones");
    } else if (30 <= h && h < 90) {  // yellows and oranges
        colorName = "yellow";
        descriptions.push(b > 0 ? "with cool undertones" : "with warm undertones");
    } else if (90 <= h && h < 150) {  // greens
        colorName = "green";
        descriptions.push(r > 0.33 * (g + b) ? "with warm undertones" : "with cool undertones");
    } else if (150 <= h && h < 210) {  // cyans
        colorName = "cyan";
        descriptions.push(r > 0.2 * (g + b) ? "with warm undertones" : "with cool undertones");
    } else if (210 <= h && h < 270) {  // blues
        colorName = "blue";
        descriptions.push(r > 0.2 * (g + b) ? "with warm undertones" : "with cool undertones");
    } else if (270 <= h && h < 330) {  // purples
        colorName = "purple";
        descriptions.push(r < b ? "with cool undertones" : "with warm undertones");
    } else {  // pinks and reds
        colorName = "pink";
        descriptions.push(b > 0.33 * (r + b) ? "with cool undertones" : "with warm undertones");
    }

    // Add the color name to the description
    descriptions.splice(2, 0, colorName);

    return descriptions.join(" ");
}

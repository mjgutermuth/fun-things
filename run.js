function getColorNameByHex(hexColor) {
    const hex = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
    const apiUrl = `https://www.thecolorapi.com/id?hex=${hex}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const colorName = data.name.value;
            const colorDescription = getColorDescription(hexColor);
            document.getElementById('colorInfoDisplay').innerText = `${colorName}: a ${colorDescription}.`;

        })
        .catch(error => console.error('Error fetching color name:', error));
}

function displayColorDescription() {
    let hexColor = document.getElementById('hexColorInput').value;
    getColorNameByHex(hexColor);
}

function getColorDescription(hexColor) {
    const color = chroma(hexColor);
    const [h, s, l] = color.hsl();

    let descriptions = [];
    let lightnessDesc = l < 0.33 ? "dark" : l <= 0.66 ? "medium" : "light";
    let brightnessDesc = s < 0.33 ? "muted" : "bright";
    
    // Calculate the color name and undertone based on hue and other factors
    let colorName = "";
    let undertoneDesc = "";

    if (h >= 0 && h < 30 || h >= 330 && h <= 360) {
        colorName = "red";
        undertoneDesc = (color.luminance() < 0.5) ? "with warm undertones" : "with cool undertones";
    } else if (h >= 30 && h < 90) {
        colorName = "yellow";
        undertoneDesc = "with warm undertones";
    } else if (h >= 90 && h < 150) {
        colorName = "green";
        undertoneDesc = "with cool undertones";
    } else if (h >= 150 && h < 210) {
        colorName = "cyan";
        undertoneDesc = "with cool undertones";
    } else if (h >= 210 && h < 270) {
        colorName = "blue";
        undertoneDesc = "with cool undertones";
    } else if (h >= 270 && h < 330) {
        colorName = "purple";
        undertoneDesc = "with cool undertones";
    } else {
        colorName = "pink";
        undertoneDesc = "with warm undertones";
    }

    descriptions.push(lightnessDesc, brightnessDesc, colorName, undertoneDesc);
    return descriptions.join(" ");
}

function displayColorDescription() {
    let hexColor = document.getElementById('hexColorInput').value;
    getColorNameByHex(hexColor);
}

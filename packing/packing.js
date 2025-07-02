// Smart packing suggestions generator
function generateSmartPackingCategories(tripData) {
    const temps = tripData.days.map(d => d.weather.temp);
    const minTemp = Math.min(...temps);
    const maxTemp = Math.max(...temps);
    const tripLength = tripData.days.length;
    
    // Detailed weather analysis
    const uvLevels = tripData.days.map(d => d.weather.uvIndex || 0);
    const maxUV = Math.max(...uvLevels);
    const highUVDays = tripData.days.filter(d => (d.weather.uvIndex || 0) >= 6).length;
    const extremeUVDays = tripData.days.filter(d => (d.weather.uvIndex || 0) >= 8).length;
    
    const humidityLevels = tripData.days.map(d => d.weather.humidity || 50);
    const avgHumidity = humidityLevels.reduce((a, b) => a + b, 0) / humidityLevels.length;
    const highHumidityDays = tripData.days.filter(d => (d.weather.humidity || 50) > 75).length;
    
    const rainDays = tripData.days.filter(d => d.weather.precipitationChance > 30).length;
    const heavyRainDays = tripData.days.filter(d => d.weather.precipitationChance > 70).length;
    
    const hotDays = tripData.days.filter(d => d.weather.temp >= 28).length;
    const veryHotDays = tripData.days.filter(d => d.weather.temp >= 32).length;
    const coldDays = tripData.days.filter(d => d.weather.temp <= 10).length;
    const freezingDays = tripData.days.filter(d => d.weather.temp <= 0).length;
    const snowDays = tripData.days.filter(d => d.weather.condition.includes('snow')).length;
    const swimWeatherDays = tripData.days.filter(d => d.weather.temp >= 24).length;
    
    const categories = {};
    
    // CLOTHING - Smart quantities and specific recommendations
    const clothingItems = [];
    if (hotDays > 0) {
        const tshirtCount = Math.min(hotDays + 1, Math.ceil(tripLength * 0.7));
        clothingItems.push(`<span class="quantity-highlight">${tshirtCount}</span> lightweight t-shirts`);
        clothingItems.push(`<span class="quantity-highlight">${Math.min(hotDays, 3)}</span> pairs of shorts`);
        
        if (highHumidityDays > 2) {
            clothingItems.push(`<span class="quantity-highlight">${Math.ceil(hotDays * 0.5)}</span> moisture-wicking shirts`);
            clothingItems.push('Quick-dry underwear for humid days');
        }
    }
    
    if (maxTemp >= 20 && minTemp >= 15) {
        clothingItems.push('1-2 light pants', '1 light sweater or cardigan');
    }
    
    if (coldDays > 0) {
        clothingItems.push('Warm jacket or coat');
        clothingItems.push(`<span class="quantity-highlight">${Math.min(coldDays + 1, 4)}</span> warm layers`);
        if (coldDays > 2) {
            clothingItems.push('Thermal underwear');
        }
    }
    
    if (snowDays > 0 || freezingDays > 0) {
        clothingItems.push('Heavy winter coat');
        clothingItems.push('Insulated gloves or mittens');
        clothingItems.push('Warm winter hat/beanie');
        clothingItems.push('Scarf or neck warmer');
        clothingItems.push(`<span class="quantity-highlight">${Math.max(snowDays, freezingDays)}</span> pairs of wool socks`);
        
        if (freezingDays > 3) {
            clothingItems.push('Face mask or balaclava');
            clothingItems.push('Hand/foot warmers');
        }
    }
    
    // Add general clothing based on trip length
    clothingItems.push(`<span class="quantity-highlight">${Math.ceil(tripLength * 0.5)}</span> pairs of pants/jeans`);
    clothingItems.push(`<span class="quantity-highlight">${tripLength + 1}</span> sets of underwear`);
    
    categories['Clothing'] = { items: clothingItems };
    
    // SWIMWEAR & BEACH GEAR
    if (swimWeatherDays >= 2) {
        const swimItems = [];
        
        if (swimWeatherDays >= 5) {
            swimItems.push('<span class="quantity-highlight">2-3</span> swimsuits/swim trunks');
            swimItems.push('Beach cover-up or sarong');
        } else {
            swimItems.push('<span class="quantity-highlight">1-2</span> swimsuits/swim trunks');
        }
        
        if (veryHotDays >= 2) {
            swimItems.push('Beach towel');
            swimItems.push('Flip-flops or water shoes');
        }
        
        if (extremeUVDays >= 2 && swimWeatherDays >= 3) {
            swimItems.push('Rash guard (UPF protection)');
            swimItems.push('Wide-brim beach hat');
        }
        
        categories['Swimwear & Beach'] = { 
            items: swimItems,
            priority: veryHotDays >= 3 ? 'medium' : undefined
        };
    }
    
    // SUN PROTECTION - Quantity-based on UV exposure
    if (highUVDays > 0 || maxTemp >= 25) {
        const sunItems = [];
        
        if (extremeUVDays >= 3) {
            sunItems.push(`<span class="quantity-highlight">SPF 50+</span> sunscreen (${Math.ceil(extremeUVDays/3)} bottles recommended)`);
            sunItems.push('UPF 50+ long-sleeve shirts');
            sunItems.push('Wide-brim sun hat with neck protection');
            sunItems.push('Zinc sunscreen for face/lips');
        } else if (highUVDays >= 2) {
            sunItems.push(`<span class="quantity-highlight">SPF 30+</span> sunscreen (${Math.ceil(highUVDays/4)} bottles)`);
            sunItems.push('Sun hat or cap');
        }
        
        if (highUVDays > 0) {
            sunItems.push('UV-protection sunglasses');
            sunItems.push('Lip balm with SPF');
        }
        
        if (hotDays >= 3 && highUVDays >= 2) {
            sunItems.push(`<span class="quantity-highlight">${Math.min(hotDays, 3)}</span> UPF clothing items`);
        }
        
        categories['Sun Protection'] = { 
            items: sunItems, 
            priority: extremeUVDays >= 2 ? 'high' : 'medium'
        };
    }
    
    // WEATHER GEAR - Specific to conditions
    if (rainDays > 0 || snowDays > 0) {
        const weatherItems = [];
        
        if (heavyRainDays >= 2) {
            weatherItems.push('Waterproof rain jacket');
            weatherItems.push('Rain pants');
            weatherItems.push('Compact umbrella + backup');
        } else if (rainDays >= 2) {
            weatherItems.push('Water-resistant jacket');
            weatherItems.push('Compact umbrella');
        }
        
        if (rainDays > 0) {
            weatherItems.push('Waterproof phone/electronics case');
            weatherItems.push(`<span class="quantity-highlight">${Math.ceil(rainDays/2)}</span> quick-dry towels`);
        }
        
        if (snowDays > 0) {
            weatherItems.push('Waterproof winter boots');
            weatherItems.push('Warm, waterproof gloves');
            weatherItems.push('Snow gaiters (if hiking)');
        }
        
        if (freezingDays > 2) {
            weatherItems.push('Ice cleats or crampons');
            weatherItems.push('Emergency blanket');
        }
        
        categories['Weather Protection'] = { 
            items: weatherItems,
            priority: heavyRainDays >= 2 || snowDays >= 2 ? 'high' : 'medium'
        };
    }
    
    // FOOTWEAR - Activity and weather specific
    const footwearItems = [];
    footwearItems.push('Comfortable walking shoes');
    
    if (hotDays >= 2) {
        footwearItems.push(`<span class="quantity-highlight">1-2</span> pairs of breathable sandals`);
    }
    
    if (swimWeatherDays >= 3) {
        footwearItems.push('Flip-flops or beach sandals');
    }
    
    if (coldDays > 0 || snowDays > 0) {
        footwearItems.push('Warm, waterproof boots');
        footwearItems.push(`<span class="quantity-highlight">${Math.min(coldDays + 2, 6)}</span> pairs of thick socks`);
    }
    
    if (rainDays > 2) {
        footwearItems.push('Waterproof shoes/boots');
    }
    
    if (freezingDays > 0) {
        footwearItems.push('Insulated winter boots');
        footwearItems.push('Wool or thermal socks');
    }
    
    categories['Footwear'] = { items: footwearItems };
    
    // ACCESSORIES - Smart essentials
    const accessoryItems = [];
    accessoryItems.push('Daypack/backpack');
    accessoryItems.push('Portable phone charger');
    accessoryItems.push('Travel adapter');
    
    if (highHumidityDays > 2) {
        accessoryItems.push('Moisture-absorbing packets');
        accessoryItems.push('Waterproof packing cubes');
    }
    
    if (extremeUVDays >= 2) {
        accessoryItems.push('Cooling towel');
        accessoryItems.push('Insulated water bottle');
    }
    
    if (freezingDays > 1) {
        accessoryItems.push('Thermal water bottle');
        accessoryItems.push('Portable hand warmers');
    }
    
    if (tripLength > 7) {
        accessoryItems.push('Laundry detergent pods');
        accessoryItems.push('Travel clothesline');
    }
    
    categories['Travel Accessories'] = { items: accessoryItems };
    
    // HEALTH & COMFORT - Condition-specific
    const healthItems = [];
    
    if (avgHumidity < 40 || freezingDays > 1) {
        healthItems.push('Extra moisturizer');
        healthItems.push('Hydrating lip balm');
    }
    
    if (highHumidityDays > 2) {
        healthItems.push('Anti-chafing balm');
        healthItems.push('Antifungal powder');
    }
    
    if (extremeUVDays >= 2) {
        healthItems.push('Aloe vera gel (sunburn relief)');
        healthItems.push('Electrolyte supplements');
    }
    
    if (coldDays > 2) {
        healthItems.push('Hand/foot warmers');
        healthItems.push('Cold weather lip protection');
    }
    
    if (freezingDays > 1) {
        healthItems.push('Frostbite prevention cream');
        healthItems.push('Emergency heat packs');
    }
    
    if (healthItems.length > 0) {
        categories['Health & Comfort'] = { items: healthItems };
    }
    
    return categories;
}
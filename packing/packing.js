// Smart packing suggestions generator
function generateSmartPackingCategories(tripData) {
    const temps = tripData.days.map(d => d.weather.temp);
    const minTemp = Math.min(...temps);
    const maxTemp = Math.max(...temps);
    const tripLength = tripData.days.length;
    
    // Get occasion data (defaults to empty if not provided)
    const occasions = tripData.occasions || {};
    const semiFormalDays = occasions.semiFormal || 0;
    const formalDays = occasions.formal || 0;
    const loungeDays = occasions.lounge || 0;
    const adventureDays = occasions.adventure || 0;
    const beachDays = occasions.beach || 0;
    const businessDays = occasions.business || 0;
    
    // Calculate casual days (what's left after special occasions)
    const specialDays = semiFormalDays + formalDays + loungeDays + adventureDays + beachDays + businessDays;
    const casualDays = Math.max(0, tripLength - specialDays);
    
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
    
    // CLOTHING - Smart quantities and specific recommendations based on occasions
    const clothingItems = [];
    
    // Formal occasions
    if (formalDays > 0) {
        clothingItems.push(`<span class="quantity-highlight">${formalDays}</span> formal outfit${formalDays > 1 ? 's' : ''} (suit/dress/gown)`);
        clothingItems.push(`<span class="quantity-highlight">${formalDays}</span> pair${formalDays > 1 ? 's' : ''} of dress shoes`);
    }
    
    // Semi-formal occasions
    if (semiFormalDays > 0) {
        clothingItems.push(`<span class="quantity-highlight">${semiFormalDays}</span> dressy outfit${semiFormalDays > 1 ? 's' : ''} (cocktail attire/blazer)`);
    }
    
    // Business days
    if (businessDays > 0) {
        clothingItems.push(`<span class="quantity-highlight">${businessDays}</span> business outfit${businessDays > 1 ? 's' : ''} (business casual/professional)`);
        if (businessDays >= 3) {
            clothingItems.push('Professional accessories (belt, watch, etc.)');
        }
    }
    
    // Lounge days
    if (loungeDays > 0) {
        clothingItems.push(`<span class="quantity-highlight">${Math.ceil(loungeDays * 0.7)}</span> comfortable lounge outfit${loungeDays > 1 ? 's' : ''} (sweats, leggings, cozy tops)`);
        if (loungeDays >= 2) {
            clothingItems.push('Slippers or cozy socks');
        }
    }
    
    // Adventure/Active days - supplement weather-based activewear
    if (adventureDays > 0) {
        clothingItems.push(`<span class="quantity-highlight">${Math.ceil(adventureDays * 1.2)}</span> activewear outfit${adventureDays > 1 ? 's' : ''} (quick-dry, durable)`);
        clothingItems.push('Sturdy hiking/adventure shoes');
        if (adventureDays >= 2) {
            clothingItems.push('Daypack for activities');
            clothingItems.push('Water bottle');
        }
    }
    
    // Weather-based additions
    if (hotDays > 0) {
        const casualHotTops = Math.min(casualDays, Math.ceil(hotDays * 0.8));
        if (casualHotTops > 0) {
            clothingItems.push(`<span class="quantity-highlight">${casualHotTops}</span> lightweight t-shirt${casualHotTops > 1 ? 's' : ''} (casual)`);
        }
        const casualShorts = Math.min(casualDays, Math.ceil(hotDays * 0.5));
        if (casualShorts > 0) {
            clothingItems.push(`<span class="quantity-highlight">${casualShorts}</span> pair${casualShorts > 1 ? 's' : ''} of shorts (casual)`);
        }
        
        if (highHumidityDays > 2) {
            clothingItems.push(`<span class="quantity-highlight">${Math.ceil(hotDays * 0.5)}</span> moisture-wicking shirt${hotDays > 2 ? 's' : ''}`);
            clothingItems.push('Quick-dry underwear for humid days');
        }
    }
    
    if (maxTemp >= 20 && minTemp >= 15 && casualDays > 0) {
        clothingItems.push('1-2 light pants (casual)');
        clothingItems.push('1 light sweater or cardigan');
    }
    
    if (coldDays > 0) {
        clothingItems.push('Warm jacket or coat');
        clothingItems.push(`<span class="quantity-highlight">${Math.min(coldDays + 1, 4)}</span> warm layer${coldDays > 1 ? 's' : ''}`);
        if (coldDays > 2) {
            clothingItems.push('Thermal underwear');
        }
    }
    
    if (snowDays > 0 || freezingDays > 0) {
        clothingItems.push('Heavy winter coat');
        clothingItems.push('Insulated gloves or mittens');
        clothingItems.push('Warm winter hat/beanie');
        clothingItems.push('Scarf or neck gaiter');
        clothingItems.push(`<span class="quantity-highlight">${Math.max(snowDays, freezingDays)}</span> pair${Math.max(snowDays, freezingDays) > 1 ? 's' : ''} of wool socks`);
        
        if (freezingDays > 3) {
            clothingItems.push('Face mask or balaclava');
            clothingItems.push('Hand/foot warmers');
        }
    }
    
    // Add general clothing based on trip length and casual days
    const totalTops = Math.ceil(tripLength * 0.7);
    clothingItems.push(`<span class="quantity-highlight">${totalTops}</span> tops total (mix of short & long sleeve)`);
    clothingItems.push(`<span class="quantity-highlight">${Math.ceil(tripLength * 0.5)}</span> pairs of pants/jeans`);
    clothingItems.push(`<span class="quantity-highlight">${tripLength + 1}</span> sets of underwear`);
    
    // Add occasion summary if any occasions specified
    if (specialDays > 0) {
        clothingItems.unshift(`<strong>Trip breakdown:</strong> ${casualDays} casual day${casualDays !== 1 ? 's' : ''}${semiFormalDays > 0 ? `, ${semiFormalDays} semi-formal` : ''}${formalDays > 0 ? `, ${formalDays} formal` : ''}${businessDays > 0 ? `, ${businessDays} business` : ''}${loungeDays > 0 ? `, ${loungeDays} lounge` : ''}${adventureDays > 0 ? `, ${adventureDays} adventure` : ''}${beachDays > 0 ? `, ${beachDays} beach` : ''}`);
    }
    
    categories['Clothing'] = { items: clothingItems };
    
    // SWIMWEAR & BEACH GEAR
    const totalBeachDays = Math.max(swimWeatherDays, beachDays); // Use whichever is higher
    if (totalBeachDays >= 2 || beachDays > 0) {
        const swimItems = [];
        
        if (beachDays > 0) {
            swimItems.push(`<strong>Beach days specified:</strong> ${beachDays}`);
        }
        
        if (totalBeachDays >= 5) {
            swimItems.push('<span class="quantity-highlight">2-3</span> swimsuits');
            swimItems.push('Beach cover-up or sarong');
        } else if (totalBeachDays >= 2) {
            swimItems.push('<span class="quantity-highlight">1-2</span> swimsuits');
        }
        
        if (veryHotDays >= 2 || beachDays >= 2) {
            swimItems.push('Beach towel');
            swimItems.push('Flip-flops or water shoes');
        }
        
        if ((extremeUVDays >= 2 && swimWeatherDays >= 3) || beachDays >= 3) {
            swimItems.push('Rash guard');
            swimItems.push('Wide-brim beach hat');
        }
        
        if (beachDays >= 2) {
            swimItems.push('Beach bag');
            swimItems.push('Waterproof phone pouch');
        }
        
        categories['Swimwear & Beach'] = { 
            items: swimItems,
            priority: (veryHotDays >= 3 || beachDays >= 3) ? 'medium' : undefined
        };
    }
    
    // SUN PROTECTION - Quantity-based on UV exposure
    if (highUVDays > 0 || maxTemp >= 25) {
        const sunItems = [];
        
        if (extremeUVDays >= 3) {
            sunItems.push(`<span class="quantity-highlight">SPF 50+</span> sunscreen`);
            sunItems.push('UPF 50+ long-sleeve shirts');
            sunItems.push('Wide-brim sun hat with neck protection');
            sunItems.push('Zinc sunscreen for face/lips');
        } else if (highUVDays >= 2) {
            sunItems.push(`<span class="quantity-highlight">SPF 30+</span> sunscreen`);
            sunItems.push('Sun hat');
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
            weatherItems.push('Compact umbrella');
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
        healthItems.push('Aloe vera gel');
        healthItems.push('Electrolyte supplements');
    }
    
    if (coldDays > 2) {
        healthItems.push('Hand/foot warmers');
        healthItems.push('Cold weather lip protection');
    }
    
    if (freezingDays > 1) {
        healthItems.push('Emergency heat packs');
    }
    
    if (healthItems.length > 0) {
        categories['Health & Comfort'] = { items: healthItems };
    }
    
    return categories;
}
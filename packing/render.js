// Weather assessment and display functions
function assessWeatherConditions(weatherData) {
    const tempHighC = weatherData.tempHigh;
    const tempLowC = weatherData.tempLow;
    const avgTempC = (tempHighC + tempLowC) / 2;
    const avgTempF = Math.round((avgTempC * 9/5) + 32);

    const humidity = weatherData.humidity;
    const precipChance = weatherData.precipitationChance;
    const uvIndex = weatherData.uvIndex;
    
    let assessment = '';
    let icon = weatherData.icon;
    
    // Severe weather always takes precedence
    if (weatherData.condition.includes('thunderstorm')) {
        assessment = weatherData.condition.includes('hail') ? 'Thunder + Hail' : 'Storms';
        icon = '⛈️';
    } else if (weatherData.condition.includes('snow')) {
        assessment = weatherData.condition.includes('heavy') ? 'Heavy Snow'
            : weatherData.condition.includes('slight') ? 'Light Snow' : 'Snow';
        icon = '❄️';
    } else {
        // Determine temperature label first
        let tempLabel, tempIcon;
        if (avgTempF >= 95) {
            tempLabel = humidity >= 70 ? 'Extreme Heat + Humidity' : 'Extreme Heat';
            tempIcon = humidity >= 70 ? '🥵' : '🔥';
        } else if (avgTempF >= 80) {
            tempLabel = humidity >= 70 ? 'Hot + Humid' : 'Hot';
            tempIcon = humidity >= 70 ? '🌡️' : '☀️';
        } else if (avgTempF >= 60) {
            tempLabel = humidity >= 70 ? 'Warm + Humid' : 'Pleasant';
            tempIcon = humidity >= 70 ? '🌫️' : '😊';
        } else if (avgTempF >= 45) {
            tempLabel = 'Cool';
            tempIcon = '🧥';
        } else if (avgTempF >= 32) {
            tempLabel = 'Cold';
            tempIcon = '❄️';
        } else {
            tempLabel = 'Freezing';
            tempIcon = '🧊';
        }

        // Overlay rain on top — combine with temp label for extremes
        if (precipChance >= 70) {
            assessment = avgTempF >= 80 ? `Heavy Rain + ${tempLabel}` : 'Heavy Rain';
            icon = '🌧️';
        } else if (precipChance >= 25) {
            assessment = avgTempF >= 95 ? `Rain + ${tempLabel}` : 'Possible Rain';
            icon = '🌦️';
        } else {
            assessment = tempLabel;
            icon = tempIcon;
        }
    }
        
    return {
        assessment: assessment,
        icon: icon,
        tempRange: getTempDisplay(avgTempC)
    };
}

function getWeatherClass(tempCelsius, condition, humidity, precipChance) {
    if (precipChance >= 25) {
        return 'weather-rain';
    }
    
    const tempF = Math.round((tempCelsius * 9/5) + 32);
    
    if (tempF > 80) return 'weather-hot';
    if (tempF >= 60) return 'weather-mild';
    if (tempF >= 45) return 'weather-cool';
    return 'weather-cold';
}

function getDataTypeLabel(dataType) {
    const labels = {
        'forecast': 'forecast',
        'current': 'current',
        'historical': 'historical',
        'estimated': 'estimated',
        'mock': 'demo data',
        'default': 'default'
    };
    return labels[dataType] || 'unknown';
}

function getCityName(location) {
    let city = location.includes(',') ? location.split(',')[0].trim() : location;

    const abbreviations = {
    // Major US cities
    'los angeles': 'LA',
    'san francisco': 'SF',
    'new york': 'NYC',
    'las vegas': 'Vegas',
    'washington': 'DC',
    'san diego': 'SD',
    'new orleans': 'NOLA',
    'san antonio': 'SA',
    'philadelphia': 'Philly',
    
    // Europe
    'london': 'London',
    'paris': 'Paris',
    'barcelona': 'BCN',
    'madrid': 'MAD',
    'amsterdam': 'AMS',
    'rome': 'Rome',
    'milan': 'Milan',
    'venice': 'Venice',
    'florence': 'Florence',
    'berlin': 'Berlin',
    'munich': 'Munich',
    'vienna': 'Vienna',
    'prague': 'Prague',
    'budapest': 'Budapest',
    'stockholm': 'STK',
    'copenhagen': 'CPH',
    'zurich': 'ZUR',
    'geneva': 'GVA',
    'brussels': 'BRU',
    'dublin': 'Dublin',
    'edinburgh': 'EDI',
    'lisbon': 'LIS',
    'athens': 'ATH',
    'istanbul': 'IST',
    'saint petersburg': 'St Pete',
    
    // Asia Pacific
    'tokyo': 'Tokyo',
    'kyoto': 'Kyoto',
    'osaka': 'Osaka',
    'bangkok': 'BKK',
    'singapore': 'SG',
    'hong kong': 'HK',
    'kuala lumpur': 'KL',
    'jakarta': 'JKT',
    'manila': 'MNL',
    'ho chi minh city': 'HCMC',
    'hanoi': 'HAN',
    'seoul': 'Seoul',
    'busan': 'Busan',
    'taipei': 'TPE',
    'beijing': 'PEK',
    'shanghai': 'SHA',
    'guangzhou': 'CAN',
    'shenzhen': 'SZX',
    'mumbai': 'BOM',
    'delhi': 'DEL',
    'bangalore': 'BLR',
    'kolkata': 'CCU',
    'chennai': 'MAA',
    'sydney': 'SYD',
    'melbourne': 'MEL',
    'brisbane': 'BNE',
    'perth': 'PER',
    'auckland': 'AKL',
    'wellington': 'WLG',
    
    // Middle East & Africa
    'dubai': 'DXB',
    'abu dhabi': 'AUH',
    'doha': 'DOH',
    'riyadh': 'RUH',
    'tel aviv': 'TLV',
    'jerusalem': 'JRS',
    'cairo': 'CAI',
    'casablanca': 'CAS',
    'marrakech': 'RAK',
    'cape town': 'CPT',
    'johannesburg': 'JHB',
    'nairobi': 'NBO',
    'lagos': 'LOS',
    
    // Americas
    'mexico city': 'CDMX',
    'guadalajara': 'GDL',
    'cancun': 'CUN',
    'playa del carmen': 'PDC',
    'toronto': 'YYZ',
    'vancouver': 'YVR',
    'montreal': 'YUL',
    'buenos aires': 'BA',
    'rio de janeiro': 'Rio',
    'são paulo': 'SP',
    'salvador': 'SSA',
    'lima': 'LIM',
    'bogota': 'BOG',
    'medellin': 'MDE',
    'santiago': 'SCL',
    'valparaiso': 'VAL',
    'montevideo': 'MVD',
    'quito': 'UIO',
    'la paz': 'LPB',
    'caracas': 'CCS',
    
    // Caribbean
    'san juan': 'SJU',
    'santo domingo': 'SDQ',
    'havana': 'HAV',
    'kingston': 'KIN',
    'nassau': 'NAS',
    'bridgetown': 'BGI'
};
    
    // Check for exact matches first
    if (abbreviations[city.toLowerCase()]) {
        return abbreviations[city.toLowerCase()];
    }

    // Smart shortening rules for unknown cities
    if (city.length <= 7) {
        return city; // Already short enough
    }
    
    // Remove common prefixes/suffixes
    city = city.replace(/^(San |Santa |Saint |St\. )/i, '');
    city = city.replace(/( City| Beach| Springs)$/i, '');
    
    // If still too long, truncate intelligently
    if (city.length > 8) {
        // Try to break at word boundaries
        const words = city.split(' ');
        if (words.length > 1) {
            // Take first word if it's reasonable length
            if (words[0].length >= 4 && words[0].length <= 8) {
                return words[0];
            }
            // Or create initials for multi-word cities
            if (words.length === 2) {
                return words[0].substring(0, 4) + words[1].substring(0, 2);
            }
        }
        
        // Last resort: truncate with ellipsis
        return city.substring(0, 6) + '..';
    }
    
    return city;
}

// Calendar rendering
function renderCalendar(tripData) {
    const calendarGrid = document.getElementById('calendarGrid');
    
    // Create trip days map
    const tripDays = new Map();
    tripData.days.forEach(day => {
        const dateKey = day.date.toISOString().split('T')[0];
        tripDays.set(dateKey, day);
    });
    
    // Calculate date range
    const firstTripDate = new Date(Math.min(...tripData.days.map(d => d.date)));
    const lastTripDate = new Date(Math.max(...tripData.days.map(d => d.date)));
    
    const startWeek = new Date(firstTripDate);
    startWeek.setDate(firstTripDate.getDate() - firstTripDate.getDay());
    
    const endWeek = new Date(lastTripDate);
    endWeek.setDate(lastTripDate.getDate() + (6 - lastTripDate.getDay()));
    
    let html = '';
    
    // Day headers
    const dayHeaders = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    dayHeaders.forEach(day => {
        html += `<div class="calendar-day-header">${day}</div>`;
    });
    
    // Calendar days
    for (let d = new Date(startWeek); d <= endWeek; d.setDate(d.getDate() + 1)) {
        const dateKey = d.toISOString().split('T')[0];
        const tripDay = tripDays.get(dateKey);
        
        const dayMonth = d.getMonth();
        const dayYear = d.getFullYear();
        const hasTripsThisMonth = tripData.days.some(td => 
            td.date.getMonth() === dayMonth && td.date.getFullYear() === dayYear
        );
        
        const isOtherMonth = !hasTripsThisMonth && !tripDay;
        
        let dayClass = 'calendar-day';
        let dayContent = '';
        
        if (isOtherMonth) {
            dayClass += ' other-month';
            dayContent = `<div class="day-number">${d.getDate()}</div>`;
        } else if (tripDay) {
            dayClass += ' trip-day';
            const weatherClass = getWeatherClass(tripDay.weather.temp, tripDay.weather.condition, tripDay.weather.humidity, tripDay.weather.precipitationChance);            dayClass += ' ' + weatherClass;
            
            const assessment = assessWeatherConditions(tripDay.weather);
            const cityName = getCityName(tripDay.location);
            
            dayContent = `
                <div class="day-header">
                    <span class="day-number">${d.getDate()}</span>
                    <span class="day-location">${cityName}</span>
                </div>
                <div class="weather-info">
                    <span class="weather-icon">${assessment.icon}</span>
                    <span class="weather-temp">${assessment.tempRange}</span>
                </div>
                <div class="weather-desc">${assessment.assessment}</div>
                <div class="data-type-indicator">${getDataTypeLabel(tripDay.weather.dataType)}</div>
            `;
        } else {
            // Regular days in trip months but not trip days
            dayContent = `<div class="day-number">${d.getDate()}</div>`;
        }
        
        html += `<div class="${dayClass}">${dayContent}</div>`;
    }
    
    calendarGrid.innerHTML = html;
    document.getElementById('packingSuggestions').style.display = 'block';
}

// Weather summary rendering
function renderWeatherSummary(tripData) {
    const temps = tripData.days.map(d => d.weather.temp);
    const uvLevels = tripData.days.map(d => d.weather.uvIndex || 0);
    const humidityLevels = tripData.days.map(d => d.weather.humidity || 50);
    const precipDays = tripData.days.filter(d => d.weather.precipitationChance > 25).length;
    
    const minTemp = Math.min(...temps);
    const maxTemp = Math.max(...temps);
    const maxUV = Math.max(...uvLevels);
    const avgHumidity = Math.round(humidityLevels.reduce((a, b) => a + b, 0) / humidityLevels.length);
    
    const highUVDays = tripData.days.filter(d => (d.weather.uvIndex || 0) >= 6).length;
    const extremeUVDays = tripData.days.filter(d => (d.weather.uvIndex || 0) >= 8).length;
    
    const summaryDiv = document.getElementById('weatherSummary');
    summaryDiv.innerHTML = `
        <h3>Trip Weather Overview</h3>
        <div class="weather-stats">
            <div class="stat-item">
                <span class="stat-label">Temperature Range</span>
                <span class="stat-value">${getTempDisplay(minTemp)} to ${getTempDisplay(maxTemp)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Max UV Index</span>
                <span class="stat-value">${Math.round(maxUV)} ${maxUV >= 8 ? '(Extreme)' : maxUV >= 6 ? '(High)' : ''}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Average Humidity</span>
                <span class="stat-value">${avgHumidity}%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Rainy Days</span>
                <span class="stat-value">${precipDays} of ${tripData.days.length} days</span>
            </div>
            ${highUVDays > 0 ? `
            <div class="stat-item">
                <span class="stat-label">High UV Days</span>
                <span class="stat-value">${highUVDays} days (UV 6+)</span>
            </div>
            ` : ''}
            ${extremeUVDays > 0 ? `
            <div class="stat-item">
                <span class="stat-label">Extreme UV Days</span>
                <span class="stat-value">${extremeUVDays} days (UV 8+)</span>
            </div>
            ` : ''}
        </div>
    `;
}

// Bag view state
let bagViewActive = false;
let _lastCategories = null;

function classifyItem(htmlText) {
    const text = htmlText.replace(/<[^>]+>/g, '').toLowerCase();
    const checkedKeywords = [
        'sunscreen', 'zinc sunscreen', 'moisturizer', 'aloe vera', 'saline nasal',
        'anti-chafing', 'antifungal', 'laundry detergent', 'electrolyte',
        'winter coat', 'heavy coat', 'waterproof boots', 'winter boots',
        'insulated boots', 'hand warmers', 'heat packs', 'emergency heat'
    ];
    return checkedKeywords.some(kw => text.includes(kw)) ? 'checked' : 'carry-on';
}

function toggleBagView() {
    bagViewActive = !bagViewActive;
    document.getElementById('bagViewBtn').textContent = bagViewActive ? 'Category View' : 'By Bag';
    renderPackingCategories();
}

function renderCategoryView(categories) {
    let html = '';
    Object.entries(categories).forEach(([category, data]) => {
        const priorityClass = data.priority ? `priority-${data.priority}` : '';
        html += `
            <div class="packing-category ${priorityClass}">
                <div class="category-title">${category}</div>
                <ul class="category-items">
                    ${data.items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    });
    return html;
}

function renderBagView(categories) {
    const carryOnItems = [];
    const checkedItems = [];

    Object.entries(categories).forEach(([categoryName, data]) => {
        data.items.forEach(item => {
            const stripped = item.replace(/<[^>]+>/g, '').trim();
            // Skip meta/summary lines
            if (!stripped || stripped.startsWith('(') || stripped.startsWith('See ') || stripped.startsWith('Trip breakdown') || stripped.startsWith('Destination reaches')) return;
            const entry = `<li><span class="item-category">${categoryName}:</span> ${item}</li>`;
            if (classifyItem(item) === 'checked') {
                checkedItems.push(entry);
            } else {
                carryOnItems.push(entry);
            }
        });
    });

    return `
        <div class="bag-view">
            <div class="bag-column">
                <div class="bag-header carry-on-header">🎒 Carry-On</div>
                <ul class="bag-items">${carryOnItems.join('')}</ul>
            </div>
            <div class="bag-column">
                <div class="bag-header checked-header">🧳 Checked Bag</div>
                <ul class="bag-items">${checkedItems.join('')}</ul>
            </div>
        </div>
    `;
}

function renderPackingCategories() {
    const packingCategories = document.getElementById('packingCategories');
    if (!_lastCategories) return;
    packingCategories.innerHTML = bagViewActive
        ? renderBagView(_lastCategories)
        : renderCategoryView(_lastCategories);
}

function renderDailyPlanner(tripData) {
    const content = document.getElementById('dailyPlannerContent');
    if (!content) return;

    let html = '';
    tripData.days.forEach(day => {
        const dateStr = day.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        const outfit = generateDailyOutfit(day.weather);
        const assessment = assessWeatherConditions(day.weather);
        const cityName = getCityName(day.location);

        html += `
            <div class="planner-day">
                <div class="planner-day-header">
                    <span class="planner-date">${dateStr}</span>
                    <span class="planner-location">${cityName}</span>
                    <span class="planner-weather">${assessment.icon} ${assessment.tempRange}</span>
                </div>
                <div class="planner-outfit">${outfit}</div>
            </div>
        `;
    });

    content.innerHTML = html;
}

function toggleDailyPlanner() {
    const content = document.getElementById('dailyPlannerContent');
    const icon = document.getElementById('plannerToggleIcon');
    const isHidden = content.style.display === 'none';
    content.style.display = isHidden ? 'block' : 'none';
    icon.textContent = isHidden ? '▼' : '▶';
}

// Main packing suggestions rendering
function renderPackingSuggestions(tripData) {
    renderWeatherSummary(tripData);
    _lastCategories = generateSmartPackingCategories(tripData);
    renderPackingCategories();
    renderDailyPlanner(tripData);
}
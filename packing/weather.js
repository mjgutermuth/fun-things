// Weather API functions
const coordsCache = new Map();
const forecastCache = new Map();

async function getLocationCoords(location) {
    if (!coordsCache.has(location)) {
        coordsCache.set(location, _fetchLocationCoords(location));
    }
    return coordsCache.get(location);
}

async function _fetchLocationCoords(location) {
    try {
        const stateAbbreviations = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
        };
        
        const searchTerms = [
            location.trim(),
            location.split(',')[0].trim(),
            location.replace(/,/g, ' ').trim()
        ];
        
        const parts = location.split(',').map(p => p.trim());
        if (parts.length === 2 && stateAbbreviations[parts[1].toUpperCase()]) {
            const fullStateName = stateAbbreviations[parts[1].toUpperCase()];
            searchTerms.push(`${parts[0]}, ${fullStateName}`);
            searchTerms.push(`${parts[0]} ${fullStateName}`);
            searchTerms.push(`${parts[0]}, ${fullStateName}, USA`);
        }
        
        searchTerms.push(`${location}, USA`);
        searchTerms.push(`${location}, United States`);
        
        for (const searchTerm of searchTerms) {
            const response = await fetch(
                `${GEOCODING_URL}?name=${encodeURIComponent(searchTerm)}&count=5&language=en&format=json`
            );
            
            if (!response.ok) continue;
            
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                const result = data.results[0];
                return {
                    latitude: result.latitude,
                    longitude: result.longitude,
                    name: result.name,
                    country: result.country || result.admin1 || ''
                };
            }
        }
        
        return null;
    } catch (error) {
        console.error('Geocoding error:', error);
        return null;
    }
}

async function fetchForecastData(coords) {
    const key = `${coords.latitude},${coords.longitude}`;
    if (!forecastCache.has(key)) {
        const url = `${WEATHER_URL}?latitude=${coords.latitude}&longitude=${coords.longitude}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,uv_index_max&hourly=relative_humidity_2m&timezone=auto&forecast_days=16`;
        forecastCache.set(key, fetch(url).then(r => {
            if (!r.ok) throw new Error(`Weather API error: ${r.status}`);
            return r.json();
        }));
    }
    return forecastCache.get(key);
}

async function getCurrentWeather(coords, targetDate) {
    try {
        const data = await fetchForecastData(coords);
        const target = new Date(targetDate).toISOString().split('T')[0];
        const dayIndex = data.daily.time.findIndex(date => date === target);

        if (dayIndex >= 0) {
            const hourStart = dayIndex * 24;
            const hourlyValues = data.hourly.relative_humidity_2m
                .slice(hourStart, hourStart + 24)
                .filter(h => h !== null);
            const avgHumidity = hourlyValues.length > 0
                ? Math.round(hourlyValues.reduce((a, b) => a + b, 0) / hourlyValues.length)
                : 50;

            return {
                temp: Math.round((data.daily.temperature_2m_max[dayIndex] + data.daily.temperature_2m_min[dayIndex]) / 2),
                tempHigh: Math.round(data.daily.temperature_2m_max[dayIndex]),
                tempLow: Math.round(data.daily.temperature_2m_min[dayIndex]),
                condition: getWeatherCondition(data.daily.weathercode[dayIndex]),
                icon: getWeatherIcon(data.daily.weathercode[dayIndex]),
                precipitation: data.daily.precipitation_sum[dayIndex] || 0,
                precipitationChance: data.daily.precipitation_probability_max[dayIndex] || 0,
                humidity: avgHumidity,
                uvIndex: data.daily.uv_index_max[dayIndex] || 0,
                dataType: 'forecast'
            };
        } else {
            const currentTemp = data.current_weather.temperature;
            return {
                temp: Math.round(currentTemp),
                tempHigh: Math.round(currentTemp + 3),
                tempLow: Math.round(currentTemp - 3),
                condition: getWeatherCondition(data.current_weather.weathercode),
                icon: getWeatherIcon(data.current_weather.weathercode),
                precipitation: 0,
                precipitationChance: 0,
                humidity: 50,
                uvIndex: 0,
                dataType: 'current'
            };
        }
    } catch (error) {
        console.error('getCurrentWeather error:', error);
        throw error;
    }
}

async function getHistoricalWeather(coords, targetDate) {
    const month = new Date(targetDate).getMonth();
    const isWinter = month < 2 || month > 10;
    const isSummer = month >= 5 && month <= 8;
    
    let baseTemp = 20;
    if (Math.abs(coords.latitude) > 60) baseTemp = 5;
    else if (Math.abs(coords.latitude) > 45) baseTemp = 15;
    else if (Math.abs(coords.latitude) < 23.5) baseTemp = 28;
    
    if (coords.latitude > 0) {
        if (isWinter) baseTemp -= 10;
        if (isSummer) baseTemp += 8;
    } else {
        if (isWinter) baseTemp += 8;
        if (isSummer) baseTemp -= 10;
    }
    
    const temp = Math.round(baseTemp + (Math.random() * 6 - 3));
    
    return {
        temp: temp,
        tempHigh: temp + 3,
        tempLow: temp - 3,
        condition: getWeatherCondition(isWinter ? 3 : 1),
        icon: getWeatherIcon(isWinter ? 3 : 1),
        precipitation: Math.random() > 0.7 ? Math.round(Math.random() * 10) : 0,
        precipitationChance: Math.random() > 0.7 ? Math.round(Math.random() * 50 + 20) : 0,
        humidity: Math.round(Math.random() * 40 + 40),
        uvIndex: Math.random() * 8,
        dataType: 'estimated'
    };
}

function getWeatherCondition(weatherCode) {
    const conditions = {
        0: 'clear sky', 1: 'mainly clear', 2: 'partly cloudy', 3: 'overcast',
        45: 'fog', 48: 'depositing rime fog',
        51: 'light drizzle', 53: 'moderate drizzle', 55: 'dense drizzle',
        61: 'slight rain', 63: 'moderate rain', 65: 'heavy rain',
        71: 'slight snow', 73: 'moderate snow', 75: 'heavy snow',
        80: 'slight rain showers', 81: 'moderate rain showers', 82: 'violent rain showers',
        95: 'thunderstorm', 96: 'thunderstorm with hail', 99: 'thunderstorm with heavy hail'
    };
    
    return conditions[weatherCode] || 'unknown';
}

function getWeatherIcon(weatherCode) {
    const icons = {
        0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️', 45: '🌫️', 48: '🌫️',
        51: '🌦️', 53: '🌦️', 55: '🌧️', 61: '🌧️', 63: '🌧️', 65: '🌧️',
        71: '❄️', 73: '❄️', 75: '❄️', 80: '🌦️', 81: '🌧️', 82: '🌧️',
        95: '⛈️', 96: '⛈️', 99: '⛈️'
    };
    
    return icons[weatherCode] || '🌤️';
}

function getMockWeatherData(location, date) {
    const month = new Date(date).getMonth();
    const isWinter = month < 2 || month > 10;
    const isSummer = month >= 5 && month <= 8;
    
    let baseTemp = 20;
    const loc = location.toLowerCase();
    
    if (loc.includes('phoenix') || loc.includes('arizona') || loc.includes('vegas')) {
        baseTemp = isSummer ? 40 : 25;
    } else if (loc.includes('seattle') || loc.includes('portland')) {
        baseTemp = isSummer ? 22 : 8;
    } else if (loc.includes('miami') || loc.includes('florida')) {
        baseTemp = isSummer ? 32 : 24;
    } else if (loc.includes('new york') || loc.includes('chicago')) {
        baseTemp = isSummer ? 26 : isWinter ? 2 : 15;
    }
    
    if (isWinter) baseTemp -= 8;
    if (isSummer) baseTemp += 5;
    
    const temp = Math.round(baseTemp + (Math.random() * 6 - 3));
    const uvIndex = isSummer ? Math.random() * 4 + 6 : Math.random() * 4 + 2;
    const humidity = loc.includes('humid') || loc.includes('florida') || loc.includes('houston') ? 
                    Math.random() * 20 + 70 : Math.random() * 30 + 40;
    
    return {
        temp: temp,
        tempHigh: temp + 3,
        tempLow: temp - 3,
        condition: temp > 30 ? 'hot and sunny' : temp < 5 ? 'cold' : 'pleasant',
        icon: temp > 30 ? '☀️' : temp < 5 ? '❄️' : '⛅',
        precipitation: Math.random() > 0.8 ? Math.round(Math.random() * 10) : 0,
        precipitationChance: Math.random() > 0.8 ? Math.round(Math.random() * 50 + 20) : 0,
        humidity: Math.round(humidity),
        uvIndex: Math.round(uvIndex),
        dataType: 'mock'
    };
}
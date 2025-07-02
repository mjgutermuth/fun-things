console.log('app.js loaded successfully!');

// Global variables
let segmentCounter = 0;
let currentTripData = null;
let tempUnit = 'F';

const GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search';
const WEATHER_URL = 'https://api.open-meteo.com/v1/forecast';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeDates();
});

function initializeDates() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const weekLater = new Date(tomorrow);
    weekLater.setDate(weekLater.getDate() + 6);

    document.getElementById('startDate').value = tomorrow.toISOString().split('T')[0];
    document.getElementById('endDate').value = weekLater.toISOString().split('T')[0];
}

function setTempUnit(unit) {
    tempUnit = unit;
    document.getElementById('celsiusBtn').classList.toggle('active', unit === 'C');
    document.getElementById('fahrenheitBtn').classList.toggle('active', unit === 'F');
    
    if (currentTripData) {
        renderCalendar(currentTripData);
        renderPackingSuggestions(currentTripData);
    }
}

function convertTemp(celsius) {
    return tempUnit === 'F' ? Math.round((celsius * 9/5) + 32) : celsius;
}

function getTempDisplay(celsius) {
    return `${convertTemp(celsius)}°${tempUnit}`;
}

// Trip segment management
function addTripSegment() {
    segmentCounter++;
    const additionalSegments = document.getElementById('additionalSegments');
    
    const segmentDiv = document.createElement('div');
    segmentDiv.className = 'segment';
    segmentDiv.id = `segment-${segmentCounter}`;
    segmentDiv.innerHTML = `
        <div class="segment-header">
            <div class="segment-title">Trip Segment ${segmentCounter}</div>
            <button class="remove-btn" onclick="removeSegment('segment-${segmentCounter}')">×</button>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Start Date</label>
                <input type="date" class="segment-start-date" required>
            </div>
            <div class="form-group">
                <label>End Date</label>
                <input type="date" class="segment-end-date" required>
            </div>
        </div>
        <div class="form-group">
            <label>Location</label>
            <input type="text" class="segment-location" placeholder="e.g., Rome, Italy" required>
        </div>
    `;
    
    additionalSegments.appendChild(segmentDiv);
}

function removeSegment(segmentId) {
    const segment = document.getElementById(segmentId);
    if (segment) segment.remove();
}

function getAllSegments() {
    const segments = [];
    
    // Main segment
    const mainStart = document.getElementById('startDate').value;
    const mainEnd = document.getElementById('endDate').value;
    const mainLocation = document.getElementById('location').value.trim();
    
    if (mainStart && mainEnd && mainLocation) {
        segments.push({ startDate: mainStart, endDate: mainEnd, location: mainLocation });
    }
    
    // Additional segments
    document.querySelectorAll('#additionalSegments .segment').forEach(segment => {
        const startDate = segment.querySelector('.segment-start-date').value;
        const endDate = segment.querySelector('.segment-end-date').value;
        const location = segment.querySelector('.segment-location').value.trim();
        
        if (startDate && endDate && location) {
            segments.push({ startDate, endDate, location });
        }
    });
    
    return segments;
}

// Main calendar generation
async function generateCalendar() {
    const segments = getAllSegments();
    
    console.log('DEBUG: segments =', segments);

    if (segments.length === 0) {
        alert('Please fill in at least the main trip details');
        return;
    }
    
    // Validate dates
    for (const segment of segments) {
        if (new Date(segment.endDate) < new Date(segment.startDate)) {
            alert(`End date must be after start date for ${segment.location}`);
            return;
        }
    }
    
    // Show loading
    document.getElementById('calendarSection').style.display = 'block';
    document.getElementById('calendarGrid').innerHTML = '<div class="loading">Generating your calendar...</div>';
    
    try {
        const tripData = await generateTripData(segments);
        currentTripData = tripData;

        renderCalendar(tripData);
        renderPackingSuggestions(tripData);
    } catch (error) {
        console.error('Error generating calendar:', error);
        document.getElementById('calendarGrid').innerHTML = '<div class="loading">Error loading weather data. Please try again.</div>';
    }
}
async function generateTripData(segments) {
    const days = [];
    
    for (const segment of segments) {
        const start = new Date(segment.startDate + 'T12:00:00');
        const end = new Date(segment.endDate + 'T12:00:00');
        
        for (let d = new Date(start); d.getTime() <= end.getTime(); d.setDate(d.getDate() + 1)) {
            const weather = await getWeatherData(segment.location, d.toISOString().split('T')[0]);
            days.push({
                date: new Date(d),
                location: segment.location,
                weather: weather
            });
        }
    }
    
    days.sort((a, b) => a.date - b.date);
    return { days, segments };
}

// Weather data fetching
async function getWeatherData(location, date) {
    console.log(`🌤️ Getting weather for: ${location} on ${date}`);
    
    try {
        const coords = await getLocationCoords(location);
        if (!coords) {
            console.log('❌ Location not found, using mock data');
            return getMockWeatherData(location, date);
        }
        
        const targetDate = new Date(date);
        const today = new Date();
        const daysFromNow = Math.ceil((targetDate - today) / (1000 * 60 * 60 * 24));
        
        let weatherData;
        
        if (daysFromNow >= -7 && daysFromNow <= 16) {
            weatherData = await getCurrentWeather(coords, date);
        } else {
            weatherData = await getHistoricalWeather(coords, date);
        }
        
        return weatherData;
        
    } catch (error) {
        console.error('❌ Weather API error, falling back to mock data:', error);
        return getMockWeatherData(location, date);
    }
}
console.log('app.js loaded successfully!');

// Global variables
let segmentCounter = 0;
let currentTripData = null;
let tempUnit = 'F';
let cruiseMode = false;

const GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search';
const WEATHER_URL = 'https://api.open-meteo.com/v1/forecast';
const ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeDates();
    restoreFormState();
    ['location', 'day0Location', 'debarkationPort'].forEach(id => {
        const el = document.getElementById(id);
        if (el) attachLocationValidation(el);
    });
});

function setCruiseMode(enabled) {
    cruiseMode = enabled;
    document.getElementById('standardModeBtn').classList.toggle('active', !enabled);
    document.getElementById('cruiseModeBtn').classList.toggle('active', enabled);
    document.getElementById('cruiseNote').style.display = enabled ? 'block' : 'none';
    document.getElementById('cruiseDateHeader').style.display = enabled ? 'block' : 'none';

    // Update main segment
    document.querySelector('#mainSegment .segment-title').textContent = enabled ? 'Embarkation Port' : 'Main Trip';
    document.querySelector('#mainSegment #location').placeholder = enabled ? 'port city, country' : 'city, state / country';
    document.querySelector('#mainSegment .standard-dates').style.display = enabled ? 'none' : 'block';
    document.querySelector('#mainSegment .cruise-day-label').style.display = enabled ? 'block' : 'none';

    // Update add button
    document.getElementById('addSegmentBtn').textContent = enabled ? '+ Add Port of Call' : '+ Add Trip Segment';

    // Show/hide debarkation section
    document.getElementById('debarkationSection').style.display = enabled ? 'block' : 'none';

    // Adjust advanced options for cruise context
    document.getElementById('businessOccasionItem').style.display = enabled ? 'none' : '';
    document.getElementById('advancedDescription').textContent = enabled
        ? 'Specify the types of nights and activities on your cruise. Sea days and unspecified days default to casual wear.'
        : 'Specify special occasions during your trip. Any unspecified days default to casual wear.';

    // Clear additional segments when switching modes to avoid stale data
    document.getElementById('additionalSegments').innerHTML = '';
    segmentCounter = 0;
}

function toggleDay0() {
    const checked = document.getElementById('day0Check').checked;
    document.getElementById('day0Segment').style.display = checked ? 'block' : 'none';
}

function toggleDebarkationPort() {
    const samePort = document.getElementById('samePortCheck').checked;
    document.getElementById('debarkationPortInput').style.display = samePort ? 'none' : 'block';
}

function getCruiseSegments() {
    const segments = [];
    const embarkDateStr = document.getElementById('embarkationDate').value;
    if (!embarkDateStr) return segments;

    const embarkBase = new Date(embarkDateStr + 'T12:00:00');

    // Day 0 — departure city
    if (document.getElementById('day0Check').checked) {
        const day0Location = document.getElementById('day0Location').value.trim();
        if (day0Location) {
            const day0Date = new Date(embarkBase);
            day0Date.setDate(day0Date.getDate() - 1);
            const day0DateStr = day0Date.toISOString().split('T')[0];
            segments.push({ startDate: day0DateStr, endDate: day0DateStr, location: day0Location });
        }
    }

    // Embarkation port — Day 1
    const embarkLocation = document.getElementById('location').value.trim();
    if (embarkLocation) {
        segments.push({ startDate: embarkDateStr, endDate: embarkDateStr, location: embarkLocation });
    }

    // Additional ports of call
    document.querySelectorAll('#additionalSegments .segment').forEach(segment => {
        const dayInput = segment.querySelector('.cruise-day-number');
        const location = segment.querySelector('.segment-location').value.trim();
        if (dayInput && dayInput.value && location) {
            const dayNumber = parseInt(dayInput.value);
            if (!isNaN(dayNumber) && dayNumber >= 1) {
                const portDate = new Date(embarkBase);
                portDate.setDate(portDate.getDate() + (dayNumber - 1));
                const portDateStr = portDate.toISOString().split('T')[0];
                segments.push({ startDate: portDateStr, endDate: portDateStr, location });
            }
        }
    });

    // Debarkation port
    const nights = parseInt(document.getElementById('cruiseNights').value);
    if (!isNaN(nights) && nights >= 1) {
        const debarkDate = new Date(embarkBase);
        debarkDate.setDate(debarkDate.getDate() + nights);
        const debarkDateStr = debarkDate.toISOString().split('T')[0];
        const samePort = document.getElementById('samePortCheck').checked;
        const debarkPort = samePort ? embarkLocation : document.getElementById('debarkationPort').value.trim();
        if (debarkPort) {
            segments.push({ startDate: debarkDateStr, endDate: debarkDateStr, location: debarkPort });
        }
    }

    segments.sort((a, b) => new Date(a.startDate) - new Date(b.startDate));
    return segments;
}

function toggleAdvancedOptions() {
    const content = document.getElementById('advancedContent');
    const toggle = document.getElementById('advancedToggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.classList.add('open');
    } else {
        content.style.display = 'none';
        toggle.classList.remove('open');
    }
}

function toggleOccasionInput(occasionType) {
    const checkbox = document.getElementById(occasionType + 'Check');
    const input = document.getElementById(occasionType + 'Input');
    
    if (checkbox.checked) {
        input.style.display = 'block';
        // Set default value to 1
        const numberInput = document.getElementById(occasionType + 'Days');
        if (!numberInput.value) {
            numberInput.value = 1;
        }
    } else {
        input.style.display = 'none';
        document.getElementById(occasionType + 'Days').value = '';
    }
}

function getOccasionData() {
    const occasions = {};
    
    const occasionTypes = ['semiFormal', 'formal', 'lounge', 'adventure', 'beach', 'business'];
    
    occasionTypes.forEach(type => {
        const checkbox = document.getElementById(type + 'Check');
        const input = document.getElementById(type + 'Days');
        
        if (checkbox && checkbox.checked && input && input.value) {
            occasions[type] = parseInt(input.value) || 0;
        }
    });
    
    return occasions;
}

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

    if (cruiseMode) {
        segmentDiv.innerHTML = `
            <div class="segment-header">
                <div class="segment-title">Port of Call</div>
                <button class="remove-btn" onclick="removeSegment('segment-${segmentCounter}')">×</button>
            </div>
            <div class="form-row cruise-port-row">
                <div class="form-group cruise-day-group">
                    <label>Day</label>
                    <input type="number" class="cruise-day-number" min="2" max="30" placeholder="#">
                </div>
                <div class="form-group">
                    <label>Port</label>
                    <div class="location-wrapper">
                        <input type="text" class="segment-location" placeholder="port city, country" required>
                        <span class="location-status"></span>
                    </div>
                    <div class="location-error-msg"></div>
                </div>
            </div>
        `;
    } else {
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
                <div class="location-wrapper">
                    <input type="text" class="segment-location" placeholder="e.g., Rome, Italy" required>
                    <span class="location-status"></span>
                </div>
                <div class="location-error-msg"></div>
            </div>
        `;
    }
    
    additionalSegments.appendChild(segmentDiv);
    const locationInput = segmentDiv.querySelector('.segment-location');
    if (locationInput) attachLocationValidation(locationInput);
}

function removeSegment(segmentId) {
    const segment = document.getElementById(segmentId);
    if (segment) segment.remove();
}

function getAllSegments() {
    if (cruiseMode) return getCruiseSegments();

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

function saveFormState() {
    try {
        localStorage.setItem('packingAssistantState', JSON.stringify({
            startDate: document.getElementById('startDate').value,
            endDate: document.getElementById('endDate').value,
            location: document.getElementById('location').value,
            tempUnit
        }));
    } catch (e) { /* ignore storage errors */ }
}

function restoreFormState() {
    try {
        const saved = localStorage.getItem('packingAssistantState');
        if (!saved) return;
        const state = JSON.parse(saved);
        if (state.startDate) document.getElementById('startDate').value = state.startDate;
        if (state.endDate) document.getElementById('endDate').value = state.endDate;
        if (state.location) document.getElementById('location').value = state.location;
        if (state.tempUnit) setTempUnit(state.tempUnit);
    } catch (e) { /* ignore storage errors */ }
}

async function validateLocationField(input) {
    const value = input.value.trim();
    const wrapper = input.closest('.location-wrapper');
    if (!wrapper) return;

    const statusEl = wrapper.querySelector('.location-status');
    const errorEl = wrapper.querySelector('.location-error-msg');

    input.classList.remove('location-valid', 'location-invalid');
    if (statusEl) statusEl.textContent = '';
    if (errorEl) errorEl.textContent = '';

    if (!value) return;

    if (statusEl) statusEl.textContent = '⏳';
    const coords = await getLocationCoords(value);

    if (coords) {
        input.classList.add('location-valid');
        if (statusEl) statusEl.textContent = '✓';
    } else {
        input.classList.add('location-invalid');
        if (statusEl) statusEl.textContent = '✗';
        if (errorEl) errorEl.textContent = 'Location not found — try adding a country or region';
    }
}

function attachLocationValidation(input) {
    input.addEventListener('blur', () => validateLocationField(input));
}

function showFormError(message) {
    const el = document.getElementById('formError');
    el.textContent = message;
    el.style.display = 'block';
}

function clearFormError() {
    document.getElementById('formError').style.display = 'none';
}

// Main calendar generation
async function generateCalendar() {
    const segments = getAllSegments();
    const occasions = getOccasionData();
    clearFormError();
    saveFormState();

    if (segments.length === 0) {
        showFormError('Please fill in at least the main trip details.');
        return;
    }

    // Validate dates
    if (!cruiseMode) {
        for (const segment of segments) {
            if (new Date(segment.endDate) < new Date(segment.startDate)) {
                showFormError(`End date must be after start date for ${segment.location}.`);
                return;
            }
        }
    }

    // Validate cruise day numbers against cruise length
    if (cruiseMode) {
        const nights = parseInt(document.getElementById('cruiseNights').value);
        if (!isNaN(nights) && nights >= 1) {
            const portInputs = document.querySelectorAll('.cruise-day-number');
            for (const input of portInputs) {
                const dayNum = parseInt(input.value);
                if (!isNaN(dayNum) && dayNum > nights) {
                    showFormError(`Day ${dayNum} exceeds your cruise length of ${nights} nights. Debarkation is on day ${nights + 1}.`);
                    return;
                }
            }
        }
    }

    // Show loading
    document.getElementById('calendarSection').style.display = 'block';
    document.getElementById('calendarGrid').innerHTML = '<div class="loading">Generating your calendar...</div>';

    try {
        const tripData = await generateTripData(segments);
        tripData.occasions = occasions;
        if (cruiseMode) {
            const nights = parseInt(document.getElementById('cruiseNights').value);
            if (!isNaN(nights) && nights >= 1) {
                tripData.effectiveTripLength = nights + 1; // nights + debarkation day
            }
            tripData.cruiseMode = true;
        }
        currentTripData = tripData;

        renderCalendar(tripData);
        renderPackingSuggestions(tripData);
    } catch (error) {
        console.error('Error generating calendar:', error);
        document.getElementById('calendarGrid').innerHTML = '<div class="loading">Error loading weather data. Please try again.</div>';
    }
}

async function generateTripData(segments) {
    const dayEntries = segments.flatMap(segment => {
        const start = new Date(segment.startDate + 'T12:00:00');
        const end = new Date(segment.endDate + 'T12:00:00');
        const entries = [];
        for (let d = new Date(start); d.getTime() <= end.getTime(); d.setDate(d.getDate() + 1)) {
            entries.push({ date: new Date(d), location: segment.location, dateStr: d.toISOString().split('T')[0] });
        }
        return entries;
    });

    const days = await Promise.all(
        dayEntries.map(({ date, location, dateStr }) =>
            getWeatherData(location, dateStr).then(weather => ({ date, location, weather }))
        )
    );

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
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = 3000;

// Ensure data directory exists
const dataDir = path.join(__dirname, 'data');
const dataFile = path.join(dataDir, 'closet.json');
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir);
}
if (!fs.existsSync(dataFile)) {
    fs.writeFileSync(dataFile, JSON.stringify({ items: [] }, null, 2));
}

// Configure multer for image uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, path.join(__dirname, 'images'));
    },
    filename: (req, file, cb) => {
        const ext = path.extname(file.originalname);
        cb(null, `${uuidv4()}${ext}`);
    }
});
const upload = multer({ storage });

// Middleware
app.use(express.json());
app.use(express.static(__dirname));

// Helper functions
function readData() {
    const raw = fs.readFileSync(dataFile, 'utf-8');
    return JSON.parse(raw);
}

function writeData(data) {
    fs.writeFileSync(dataFile, JSON.stringify(data, null, 2));
}

// API Routes

// Get all items
app.get('/api/items', (req, res) => {
    const data = readData();
    res.json(data.items);
});

// Add new item
app.post('/api/items', upload.single('image'), (req, res) => {
    const data = readData();
    const newItem = {
        id: uuidv4(),
        name: req.body.name,
        category: req.body.category,
        color: req.body.color,
        season: JSON.parse(req.body.season || '[]'),
        image: req.file ? `images/${req.file.filename}` : null,
        createdAt: new Date().toISOString()
    };
    data.items.push(newItem);
    writeData(data);
    res.status(201).json(newItem);
});

// Update item
app.put('/api/items/:id', upload.single('image'), (req, res) => {
    const data = readData();
    const index = data.items.findIndex(item => item.id === req.params.id);
    if (index === -1) {
        return res.status(404).json({ error: 'Item not found' });
    }

    const existingItem = data.items[index];
    const updatedItem = {
        ...existingItem,
        name: req.body.name || existingItem.name,
        category: req.body.category || existingItem.category,
        color: req.body.color || existingItem.color,
        season: req.body.season ? JSON.parse(req.body.season) : existingItem.season
    };

    if (req.file) {
        // Delete old image if it exists
        if (existingItem.image) {
            const oldImagePath = path.join(__dirname, existingItem.image);
            if (fs.existsSync(oldImagePath)) {
                fs.unlinkSync(oldImagePath);
            }
        }
        updatedItem.image = `images/${req.file.filename}`;
    }

    data.items[index] = updatedItem;
    writeData(data);
    res.json(updatedItem);
});

// Delete item
app.delete('/api/items/:id', (req, res) => {
    const data = readData();
    const index = data.items.findIndex(item => item.id === req.params.id);
    if (index === -1) {
        return res.status(404).json({ error: 'Item not found' });
    }

    const item = data.items[index];
    // Delete associated image
    if (item.image) {
        const imagePath = path.join(__dirname, item.image);
        if (fs.existsSync(imagePath)) {
            fs.unlinkSync(imagePath);
        }
    }

    data.items.splice(index, 1);
    writeData(data);
    res.status(204).send();
});

app.listen(PORT, () => {
    console.log(`Closet app running at http://localhost:${PORT}`);
});

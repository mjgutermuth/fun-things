// State
let items = [];
let currentEditId = null;

// DOM Elements
const itemsGrid = document.getElementById('items-grid');
const emptyState = document.getElementById('empty-state');
const modal = document.getElementById('item-modal');
const form = document.getElementById('item-form');
const modalTitle = document.getElementById('modal-title');
const deleteBtn = document.getElementById('delete-btn');
const filterCategory = document.getElementById('filter-category');
const imageInput = document.getElementById('item-image');
const imagePreview = document.getElementById('image-preview');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadItems();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('add-item-btn').addEventListener('click', openAddModal);
    document.querySelector('.close-btn').addEventListener('click', closeModal);
    document.querySelector('.cancel-btn').addEventListener('click', closeModal);
    form.addEventListener('submit', handleSubmit);
    deleteBtn.addEventListener('click', handleDelete);
    filterCategory.addEventListener('change', renderItems);
    imageInput.addEventListener('change', handleImagePreview);

    // Close modal on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
}

// API Functions
async function loadItems() {
    try {
        const response = await fetch('/api/items');
        items = await response.json();
        renderItems();
    } catch (error) {
        console.error('Failed to load items:', error);
    }
}

async function saveItem(formData) {
    const url = currentEditId ? `/api/items/${currentEditId}` : '/api/items';
    const method = currentEditId ? 'PUT' : 'POST';

    const response = await fetch(url, {
        method,
        body: formData
    });

    if (!response.ok) throw new Error('Failed to save item');
    return response.json();
}

async function deleteItem(id) {
    const response = await fetch(`/api/items/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete item');
}

// Render Functions
function renderItems() {
    const filter = filterCategory.value;
    const filtered = filter
        ? items.filter(item => item.category === filter)
        : items;

    if (filtered.length === 0) {
        itemsGrid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    itemsGrid.style.display = 'grid';
    emptyState.style.display = 'none';

    itemsGrid.innerHTML = filtered.map(item => `
        <div class="item-card" data-id="${item.id}">
            <div class="item-image">
                ${item.image
                    ? `<img src="${item.image}" alt="${item.name}">`
                    : '<div class="no-image">No image</div>'}
            </div>
            <div class="item-info">
                <h4>${item.name}</h4>
                <span class="category-badge ${item.category}">${item.category}</span>
                ${item.color ? `<span class="color-tag">${item.color}</span>` : ''}
            </div>
        </div>
    `).join('');

    // Add click listeners to cards
    document.querySelectorAll('.item-card').forEach(card => {
        card.addEventListener('click', () => openEditModal(card.dataset.id));
    });
}

// Modal Functions
function openAddModal() {
    currentEditId = null;
    modalTitle.textContent = 'Add Item';
    deleteBtn.style.display = 'none';
    form.reset();
    imagePreview.innerHTML = '';
    modal.classList.add('open');
}

function openEditModal(id) {
    const item = items.find(i => i.id === id);
    if (!item) return;

    currentEditId = id;
    modalTitle.textContent = 'Edit Item';
    deleteBtn.style.display = 'block';

    document.getElementById('item-id').value = item.id;
    document.getElementById('item-name').value = item.name;
    document.getElementById('item-category').value = item.category;
    document.getElementById('item-color').value = item.color || '';

    // Set season checkboxes
    document.querySelectorAll('input[name="season"]').forEach(cb => {
        cb.checked = item.season?.includes(cb.value) || false;
    });

    // Show current image
    if (item.image) {
        imagePreview.innerHTML = `<img src="${item.image}" alt="Current image">`;
    } else {
        imagePreview.innerHTML = '';
    }

    modal.classList.add('open');
}

function closeModal() {
    modal.classList.remove('open');
    currentEditId = null;
    form.reset();
    imagePreview.innerHTML = '';
}

// Form Handlers
function handleImagePreview(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
}

async function handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append('name', document.getElementById('item-name').value);
    formData.append('category', document.getElementById('item-category').value);
    formData.append('color', document.getElementById('item-color').value);

    const seasons = Array.from(document.querySelectorAll('input[name="season"]:checked'))
        .map(cb => cb.value);
    formData.append('season', JSON.stringify(seasons));

    const imageFile = imageInput.files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    try {
        const savedItem = await saveItem(formData);

        if (currentEditId) {
            const index = items.findIndex(i => i.id === currentEditId);
            items[index] = savedItem;
        } else {
            items.push(savedItem);
        }

        renderItems();
        closeModal();
    } catch (error) {
        console.error('Failed to save item:', error);
        alert('Failed to save item. Please try again.');
    }
}

async function handleDelete() {
    if (!currentEditId) return;

    if (!confirm('Are you sure you want to delete this item?')) return;

    try {
        await deleteItem(currentEditId);
        items = items.filter(i => i.id !== currentEditId);
        renderItems();
        closeModal();
    } catch (error) {
        console.error('Failed to delete item:', error);
        alert('Failed to delete item. Please try again.');
    }
}

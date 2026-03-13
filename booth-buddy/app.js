/* ── CONSTANTS ── */

const PACING = [
    { id: 'normal',    label: 'normal' },
    { id: 'build',     label: 'build ↑' },
    { id: 'pull-back', label: 'pull back ↓' },
];

const ENERGY = [
    { id: 'soft',   label: 'soft' },
    { id: 'medium', label: 'medium' },
    { id: 'big',    label: 'big' },
];


/* ── STATE ── */

const state = {
    lines: [],       // { id, text, isBeatStart, isTurn, vibe, intention, pacing, energy, notes }
    brief: '',
    selectedId: null,
    markupHistory: {}, // lineId -> previous text (one level undo)
};


/* ── UTILS ── */

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function showView(id) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');
}

function getLine(id) {
    return state.lines.find(l => l.id === id);
}


/* ── SCRIPT PARSING ── */

function parseScript(raw) {
    return raw
        .split('\n')
        .map(l => l.trim())
        .filter(Boolean)
        .map((text, i) => ({
            id: i,
            text,
            isBeatStart: false,
            isTurn: false,
            vibe: '',
            intention: '',
            pacing: null,
            energy: null,
            notes: '',
        }));
}


/* ── ANNOTATE VIEW: RENDERING ── */

function renderScriptPanel() {
    const panel = document.getElementById('script-panel');
    panel.innerHTML = '';

    state.lines.forEach(line => {
        const block = document.createElement('div');
        block.className = 'line-block';
        block.dataset.id = line.id;

        if (state.selectedId === line.id) block.classList.add('selected');

        const chips = buildChips(line);

        block.innerHTML = `
            ${buildBeatBar(line)}
            <span class="line-num">${line.id + 1}</span>
            ${chips ? `<div class="line-meta">${chips}</div>` : ''}
            <div class="line-content"></div>
            ${line.notes ? `<div class="line-note-preview">${escapeHtml(line.notes)}</div>` : ''}
        `;

        block.querySelector('.line-content').textContent = line.text;
        wireLineEvents(block, line);
        panel.appendChild(block);
    });
}

function buildBeatBar(line) {
    if (!line.isBeatStart) return '';

    const parts = [];
    if (line.vibe)      parts.push(`<span class="beat-bar-anno">${escapeHtml(line.vibe)}</span>`);
    if (line.intention) parts.push(`<span class="beat-bar-anno intention">${escapeHtml(line.intention)}</span>`);

    return `
        <div class="beat-bar">
            <span class="beat-bar-rule"></span>
            <span class="beat-bar-label">beat</span>
            <span class="beat-bar-rule"></span>
            ${parts.join('<span class="beat-bar-sep">·</span>')}
        </div>
    `;
}

function buildChips(line) {
    const parts = [];
    if (line.isTurn) {
        parts.push(`<span class="line-chip chip-turn">↕ turn</span>`);
    }
    // show vibe/intention chips only on non-beat-start lines
    // (beat-start lines show them in the beat bar)
    if (line.vibe && !line.isBeatStart) {
        parts.push(`<span class="line-chip chip-vibe">${escapeHtml(line.vibe)}</span>`);
    }
    if (line.intention && !line.isBeatStart) {
        parts.push(`<span class="line-chip chip-intention">${escapeHtml(line.intention)}</span>`);
    }
    if (line.pacing && line.pacing !== 'normal') {
        const p = PACING.find(x => x.id === line.pacing);
        if (p) parts.push(`<span class="line-chip chip-meta">${p.label}</span>`);
    }
    if (line.energy && line.energy !== 'medium') {
        const e = ENERGY.find(x => x.id === line.energy);
        if (e) parts.push(`<span class="line-chip chip-meta">${e.label}</span>`);
    }
    return parts.join('');
}

function wireLineEvents(block, line) {
    block.addEventListener('mousedown', () => {
        if (state.selectedId !== line.id) selectLine(line.id, block);
    });
}

function refreshLineBlock(line) {
    const block = document.querySelector(`.line-block[data-id="${line.id}"]`);
    if (!block) return;

    // Re-render beat bar
    const existingBar = block.querySelector('.beat-bar');
    if (line.isBeatStart) {
        const html = buildBeatBar(line);
        if (existingBar) {
            existingBar.outerHTML = html;
        } else {
            block.insertAdjacentHTML('afterbegin', html);
        }
    } else if (existingBar) {
        existingBar.remove();
    }

    // Re-render chips
    let metaEl = block.querySelector('.line-meta');
    const chips = buildChips(line);
    if (chips) {
        if (!metaEl) {
            metaEl = document.createElement('div');
            metaEl.className = 'line-meta';
            block.insertBefore(metaEl, block.querySelector('.line-content'));
        }
        metaEl.innerHTML = chips;
    } else if (metaEl) {
        metaEl.remove();
    }
}

function updateNotePreview(line) {
    const block = document.querySelector(`.line-block[data-id="${line.id}"]`);
    if (!block) return;
    let noteEl = block.querySelector('.line-note-preview');
    if (line.notes) {
        if (!noteEl) {
            noteEl = document.createElement('div');
            noteEl.className = 'line-note-preview';
            block.appendChild(noteEl);
        }
        noteEl.textContent = line.notes;
    } else if (noteEl) {
        noteEl.remove();
    }
}


/* ── ANNOTATE VIEW: SELECTION & SIDEBAR ── */

function selectLine(id, blockEl) {
    document.querySelectorAll('.line-block.selected').forEach(el => el.classList.remove('selected'));
    blockEl.classList.add('selected');
    state.selectedId = id;
    renderSidebar(getLine(id));
}

function renderSidebar(line) {
    document.getElementById('sidebar-empty').classList.add('hidden');
    document.getElementById('sidebar-tools').classList.remove('hidden');

    document.getElementById('sidebar-line-num').textContent = `line ${line.id + 1}`;

    // beat toggle
    const beatBtn = document.getElementById('beat-toggle');
    beatBtn.classList.toggle('active', line.isBeatStart);
    beatBtn.textContent = line.isBeatStart ? 'beat start' : 'mark beat start';
    beatBtn.onmousedown = e => {
        e.preventDefault();
        line.isBeatStart = !line.isBeatStart;
        refreshLineBlock(line);
        renderSidebar(line);
    };

    // turn toggle
    const turnBtn = document.getElementById('turn-toggle');
    turnBtn.classList.toggle('active', line.isTurn);
    turnBtn.textContent = line.isTurn ? 'turn' : 'mark turn';
    turnBtn.onmousedown = e => {
        e.preventDefault();
        line.isTurn = !line.isTurn;
        refreshLineBlock(line);
        renderSidebar(line);
    };

    // vibe
    const vibeInput = document.getElementById('vibe-input');
    vibeInput.value = line.vibe;
    vibeInput.oninput = () => {
        line.vibe = vibeInput.value;
        refreshLineBlock(line);
    };

    // intention
    const intentionInput = document.getElementById('intention-input');
    intentionInput.value = line.intention;
    intentionInput.oninput = () => {
        line.intention = intentionInput.value;
        refreshLineBlock(line);
    };

    // pacing
    document.querySelectorAll('.pacing-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.pacing === line.pacing);
        btn.onmousedown = e => {
            e.preventDefault();
            line.pacing = line.pacing === btn.dataset.pacing ? null : btn.dataset.pacing;
            refreshLineBlock(line);
            renderSidebar(line);
        };
    });

    // energy
    document.querySelectorAll('.energy-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.energy === line.energy);
        btn.onmousedown = e => {
            e.preventDefault();
            line.energy = line.energy === btn.dataset.energy ? null : btn.dataset.energy;
            refreshLineBlock(line);
            renderSidebar(line);
        };
    });

    // notes
    const notesInput = document.getElementById('line-notes');
    notesInput.value = line.notes;
    notesInput.oninput = () => {
        line.notes = notesInput.value;
        updateNotePreview(line);
    };
}


/* ── DELIVERY MARKER INSERTION ── */

function insertMarker(text) {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return;

    const range = sel.getRangeAt(0);

    // startContainer must be a text node inside .line-content —
    // if it's the element itself, offsets are child indices, not characters
    const startNode = range.startContainer;
    if (startNode.nodeType !== Node.TEXT_NODE) return;
    const lineContent = startNode.parentElement;
    if (!lineContent || !lineContent.classList.contains('line-content')) return;

    const block = lineContent.closest('.line-block');
    if (!block) return;

    const lineId = parseInt(block.dataset.id);
    const line = getLine(lineId);
    if (!line) return;

    const start = Math.min(range.startOffset, line.text.length);
    const end   = range.endContainer === startNode
        ? Math.min(range.endOffset, line.text.length)
        : line.text.length;

    const before   = line.text.slice(0, start);
    const selected = line.text.slice(start, end);
    const after    = line.text.slice(end);

    state.markupHistory[lineId] = line.text;

    if (text === '**' || text === '~~' || text === '[]') {
        if (!selected) return;
        if (text === '[]') {
            line.text = before + `[${selected}]` + after;
        } else {
            const ch = text === '**' ? '*' : '~';
            line.text = before + `${ch}${selected}${ch}` + after;
        }
    } else {
        line.text = before + text + after;
    }

    sel.removeAllRanges();
    lineContent.textContent = line.text;

    if (lineId !== state.selectedId) selectLine(lineId, block);
}


/* ── BOOTH VIEW ── */

function renderBooth() {
    const script = document.getElementById('booth-script');
    script.innerHTML = '';

    document.getElementById('booth-brief-bar').textContent = state.brief
        ? state.brief.split('\n')[0].slice(0, 120)
        : '';

    state.lines.forEach(line => {
        if (line.isBeatStart) {
            const divider = document.createElement('div');
            divider.className = 'booth-beat-divider';

            const annoParts = [];
            if (line.vibe)      annoParts.push(`<span class="booth-beat-vibe">${escapeHtml(line.vibe)}</span>`);
            if (line.intention) annoParts.push(`<span class="booth-beat-intention">${escapeHtml(line.intention)}</span>`);

            divider.innerHTML = `
                <div class="booth-beat-rule"></div>
                <span class="booth-beat-label">beat</span>
                <div class="booth-beat-rule"></div>
                ${annoParts.join('<span class="booth-beat-sep">·</span>')}
            `;
            script.appendChild(divider);
        }

        const block = document.createElement('div');
        block.className = 'booth-line';
        if (line.isTurn) block.classList.add('is-turn');

        const tagParts = [];
        if (line.isTurn) {
            tagParts.push(`<span class="booth-tag booth-tag-turn">↕ turn</span>`);
        }
        if (line.vibe && !line.isBeatStart) {
            tagParts.push(`<span class="booth-tag booth-tag-vibe">${escapeHtml(line.vibe)}</span>`);
        }
        if (line.intention && !line.isBeatStart) {
            tagParts.push(`<span class="booth-tag booth-tag-intention">${escapeHtml(line.intention)}</span>`);
        }
        if (line.pacing && line.pacing !== 'normal') {
            const p = PACING.find(x => x.id === line.pacing);
            if (p) tagParts.push(`<span class="booth-tag dim">${p.label}</span>`);
        }
        if (line.energy && line.energy !== 'medium') {
            const e = ENERGY.find(x => x.id === line.energy);
            if (e) tagParts.push(`<span class="booth-tag dim">${e.label}</span>`);
        }

        const notesHtml = line.notes
            ? `<div class="booth-line-notes">${escapeHtml(line.notes)}</div>`
            : '';

        block.innerHTML = `
            <div class="booth-line-header">
                <span class="booth-line-num">${line.id + 1}</span>
                <div class="booth-tags">${tagParts.join('')}</div>
            </div>
            <div class="booth-line-text">${renderBoothText(line.text)}</div>
            ${notesHtml}
        `;

        script.appendChild(block);
    });
}

function renderBoothText(text) {
    const t = text
        .replace(/\/\//g,          '\x00BR\x00')
        .replace(/\//g,            '\x00PA\x00')
        .replace(/\*([^*]+)\*/g,   '\x00AS\x00$1\x00AE\x00')
        .replace(/~([^~]+)~/g,     '\x00ZS\x00$1\x00ZE\x00')
        .replace(/\[([^\]]+)\]/g,  '\x00PS\x00$1\x00PE\x00')
        .replace(/↩/g,             '\x00PB\x00');

    return escapeHtml(t)
        .replace(/\x00BR\x00/g, '<span class="mark-breath">╱╱</span>')
        .replace(/\x00PA\x00/g, '<span class="mark-pause">╱</span>')
        .replace(/\x00AS\x00/g, '<span class="mark-arc">')
        .replace(/\x00AE\x00/g, '</span>')
        .replace(/\x00ZS\x00/g, '<span class="mark-zhoosh">')
        .replace(/\x00ZE\x00/g, '</span>')
        .replace(/\x00PS\x00/g, '<span class="mark-product">[')
        .replace(/\x00PE\x00/g, ']</span>')
        .replace(/\x00PB\x00/g, '<span class="mark-pullback">↩</span>');
}


/* ── INIT ── */

document.addEventListener('DOMContentLoaded', () => {

    // Input view
    document.getElementById('prep-btn').addEventListener('click', () => {
        const raw = document.getElementById('script-input').value.trim();
        if (!raw) return;

        state.brief  = document.getElementById('brief-input').value.trim();
        state.lines  = parseScript(raw);
        state.selectedId = null;

        renderScriptPanel();

        document.getElementById('sidebar-empty').classList.remove('hidden');
        document.getElementById('sidebar-tools').classList.add('hidden');
        document.getElementById('brief-content').textContent = state.brief;
        document.getElementById('brief-panel').classList.add('hidden');

        showView('view-annotate');
    });

    // Annotate view
    document.getElementById('back-to-input').addEventListener('click', () => {
        showView('view-input');
    });

    document.getElementById('brief-toggle').addEventListener('click', () => {
        document.getElementById('brief-panel').classList.toggle('hidden');
    });

    document.getElementById('enter-booth').addEventListener('click', () => {
        renderBooth();
        showView('view-booth');
    });

    // Delivery marker buttons
    document.querySelectorAll('.beat-btn').forEach(btn => {
        btn.addEventListener('mousedown', e => {
            e.preventDefault();
            insertMarker(btn.dataset.insert);
        });
    });

    // Undo last marker (Cmd/Ctrl+Z) while in annotate view
    document.addEventListener('keydown', e => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'z' && state.selectedId !== null) {
            const prev = state.markupHistory[state.selectedId];
            if (prev === undefined) return;
            e.preventDefault();
            const line = getLine(state.selectedId);
            line.text = prev;
            delete state.markupHistory[state.selectedId];
            const block = document.querySelector(`.line-block[data-id="${state.selectedId}"]`);
            if (block) block.querySelector('.line-content').textContent = line.text;
        }
    });

    // Booth view
    document.getElementById('exit-booth').addEventListener('click', () => {
        showView('view-annotate');
    });

    document.getElementById('print-btn').addEventListener('click', () => {
        window.print();
    });
});

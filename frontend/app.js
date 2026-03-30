// --- UI Helpers ---
function toggleFormula() {
    const overlay = document.getElementById('formula-overlay');
    overlay.classList.toggle('hidden');
}

// --- Configuration ---
const API_BASE = 'http://localhost:3000/api';
let currentMachine = {
    states: ["q0", "q1", "q2", "q3", "q4"],
    input: "aabb",
    tape: ["a", "a", "b", "b", "_"],
    head: 0,
    currentState: "q0",
    transitions: {
        "q0,a": ["q1", "X", "R"],
        "q1,a": ["q1", "a", "R"],
        "q1,Y": ["q1", "Y", "R"],
        "q1,b": ["q2", "Y", "L"],
        "q2,Y": ["q2", "Y", "L"],
        "q2,a": ["q2", "a", "L"],
        "q2,X": ["q0", "X", "R"],
        "q0,Y": ["q3", "Y", "R"],
        "q3,Y": ["q3", "Y", "R"],
        "q3,_": ["q4", "_", "R"]
    },
    status: 'RUNNING',
    stepCount: 0
};

let cy; // Cytoscape instance
let isRunning = false;
let runTimeout = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initTape();
    initGraph();
    updateUI();
    
    // Chat Form
    document.getElementById('chat-form').addEventListener('submit', (e) => {
        e.preventDefault();
        handleChatInput();
    });

    // Speed Control
    document.getElementById('speed-control').addEventListener('input', (e) => {
        if (isRunning) {
            clearTimeout(runTimeout);
            runAuto();
        }
    });

    // Load custom machine if selected
    document.getElementById('problem-selector').addEventListener('change', async (e) => {
        const problemId = e.target.value;
        if (!problemId) return;
        
        if (['palindrome', 'anbncn', 'parity'].includes(problemId)) {
             callBackendAI(problemId);
             return;
        }

        try {
            const resp = await fetch(`${API_BASE}/problems`);
            const problems = await resp.json();
            const prob = problems.find(p => p.id === problemId);
            if (prob) {
                currentMachine = { ...prob.machine, status: 'RUNNING', stepCount: 0 };
                document.getElementById('input-string').value = currentMachine.input;
                initTape();
                initGraph();
                updateUI();
                addChatMessage(`Loaded ${prob.name}: ${prob.description}`, 'ai');
            }
        } catch (err) {
            console.error("Failed to load problem", err);
        }
    });
});

// --- UI Logic ---
function switchView(view) {
    document.getElementById('view-tape').classList.add('hidden');
    document.getElementById('view-table').classList.add('hidden');
    document.getElementById('view-graph').classList.add('hidden');
    
    // Deactivate all buttons
    document.querySelectorAll('[onclick^="switchView"]').forEach(btn => btn.classList.remove('tab-active'));
    
    // Activate target
    document.getElementById(`view-${view}`).classList.remove('hidden');
    const sourceBtn = Array.from(document.querySelectorAll('[onclick^="switchView"]')).find(btn => btn.getAttribute('onclick').includes(view));
    if (sourceBtn) sourceBtn.classList.add('tab-active');

    if (view === 'graph') {
        setTimeout(() => {
            cy.resize();
            cy.fit();
        }, 100);
    }
    if (view === 'table') {
        renderTable();
    }
}

function updateUI() {
    document.getElementById('current-step-display').innerText = currentMachine.stepCount || 0;
    document.getElementById('current-state-display').innerText = currentMachine.currentState;
    
    // Highlight graph state
    if (cy) {
        cy.nodes().removeClass('active');
        cy.nodes(`[id="${currentMachine.currentState}"]`).addClass('active');
    }

    // Status Styling
    const tapeContainer = document.querySelector('.tape-container');
    tapeContainer.classList.remove('accept-glow', 'reject-shake');
    
    if (currentMachine.status === 'ACCEPTED') {
        tapeContainer.classList.add('accept-glow');
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#22c55e', '#ffffff', '#4f46e5']
        });
        document.getElementById('action-text-display').innerHTML = `<span class="bg-emerald-500 text-dark px-4 py-1 rounded-full font-bold animate-bounce shadow-lg shadow-emerald-500/50">✅ STRING ACCEPTED!</span>`;
        isRunning = false;
    } else if (currentMachine.status === 'REJECTED') {
        tapeContainer.classList.add('reject-shake');
        document.getElementById('action-text-display').innerHTML = `<span class="bg-red-500 text-white px-4 py-1 rounded-full font-bold shadow-lg shadow-red-500/50">❌ STRING REJECTED</span>`;
        isRunning = false;
    }
}

// --- Tape Visualization ---
function initTape() {
    const tapeContent = document.getElementById('tape-content');
    tapeContent.innerHTML = '';
    
    // Ensure we have some margin padding on tape for smoothness
    const renderTape = [...currentMachine.tape];
    if (renderTape.length < 15) {
        for(let i=0; i<10; i++) renderTape.push('_');
    }
    
    renderTape.forEach((symbol, idx) => {
        const cell = document.createElement('div');
        cell.className = `tape-cell transition-all duration-300 ${idx === currentMachine.head ? 'active' : ''}`;
        cell.innerText = symbol;
        cell.id = `cell-${idx}`;
        tapeContent.appendChild(cell);
    });

    moveHeadToActive();
}

function updateTape(oldHead, newHead, writeSymbol) {
    const cells = document.querySelectorAll('.tape-cell');
    
    // Update old cell if symbol changed
    const oldCell = document.getElementById(`cell-${oldHead}`);
    if (oldCell && oldCell.innerText !== writeSymbol) {
        oldCell.innerText = writeSymbol;
        oldCell.classList.add('cell-update');
        setTimeout(() => oldCell.classList.remove('cell-update'), 400);
    }

    // Update active marker
    cells.forEach(c => c.classList.remove('active'));
    
    // Check if we need more cells
    if (newHead >= cells.length || newHead < 0) {
        initTape(); // Full re-render if expanded for simplicity in this demo
        return;
    }

    const newCell = document.getElementById(`cell-${newHead}`);
    if (newCell) {
        newCell.classList.add('active');
        moveHeadToActive();
    }
}

function moveHeadToActive() {
    const tapeContent = document.getElementById('tape-content');
    const activeCell = document.querySelector('.tape-cell.active');
    if (activeCell) {
        const offset = activeCell.offsetLeft;
        const viewportWidth = document.getElementById('tape-viewport').offsetWidth;
        // Center the active cell
        const translateX = (viewportWidth / 2) - offset - 30; // 30 is half of cell width
        tapeContent.style.transform = `translateX(${translateX}px)`;
    }
}

// --- Simulation logic via Backend ---
async function stepSim() {
    if (currentMachine.status !== 'RUNNING') return;

    try {
        const oldHead = currentMachine.head;
        const response = await fetch(`${API_BASE}/simulate-step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentMachine)
        });
        
        const nextMachine = await response.json();
        
        // Update model
        const writeSymbol = nextMachine.tape[oldHead];
        currentMachine = nextMachine;
        currentMachine.stepCount = (currentMachine.stepCount || 0) + 1;

        // Update View
        updateTape(oldHead, currentMachine.head, writeSymbol);
        updateUI();
        
        document.getElementById('action-text-display').innerText = currentMachine.action;
        document.getElementById('action-text-display').className = "mt-auto text-center text-accent/80 font-mono text-sm";
        
        return currentMachine.status;
    } catch (err) {
        console.error("Simulation error", err);
        return 'ERROR';
    }
}

async function runAuto() {
    if (!isRunning) return;
    const status = await stepSim();
    if (status === 'RUNNING') {
        const speed = document.getElementById('speed-control').value;
        runTimeout = setTimeout(runAuto, 2100 - speed); // Invert speed slider logic
    } else {
        isRunning = false;
    }
}

function runSim() {
    if (currentMachine.status !== 'RUNNING') {
        resetSim();
        setTimeout(() => {
            isRunning = true;
            runAuto();
        }, 500);
        return;
    }
    isRunning = !isRunning;
    if (isRunning) runAuto();
}

function resetSim() {
    isRunning = false;
    clearTimeout(runTimeout);
    
    const inputStr = document.getElementById('input-string').value || "aabb";
    currentMachine.tape = inputStr.split('').concat(['_', '_', '_', '_', '_', '_']);
    currentMachine.head = 0;
    currentMachine.currentState = "q0";
    currentMachine.status = 'RUNNING';
    currentMachine.stepCount = 0;
    
    // Ensure transitions match the latest anbn if that's what we are resetting to
    // (In a real app, this would depend on the active problem id)
    
    initTape();
    updateUI();
    document.getElementById('action-text-display').innerText = "Machine reset.";
}

function loadInput() {
    resetSim();
}

// --- Graph Visualization ---
function initGraph() {
    const elements = [];
    const states = currentMachine.states;
    
    // Dynamically calculate node positions in a grid layout
    const cols = Math.min(states.length, 3); // max 3 per row
    const rows = Math.ceil(states.length / cols);
    const spacingX = 200;
    const spacingY = 200;
    
    const nodePositions = {};
    states.forEach((s, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        nodePositions[s] = { x: 100 + col * spacingX, y: 150 + row * spacingY };
    });

    // Detect accept/final states dynamically
    const acceptStates = states.filter(s => 
        s.includes('accept') || s.includes('final') || 
        s === states[states.length - 1] // last state is usually the accept state
    );

    // Hidden start point for initial arrow
    const startPos = { x: nodePositions[states[0]].x - 100, y: nodePositions[states[0]].y };
    elements.push({ data: { id: 'start', label: '' }, position: startPos, classes: 'start-node' });

    // Add state nodes
    states.forEach(s => {
        const classes = acceptStates.includes(s) ? 'accept-state' : '';
        elements.push({ 
            data: { id: s, label: s },
            position: nodePositions[s],
            classes: classes
        });
    });

    // Initial arrow pointing to q0
    elements.push({ data: { id: 'init-arrow', source: 'start', target: states[0] } });

    // Edges from transitions
    Object.keys(currentMachine.transitions).forEach(key => {
        const [fromState, readSym] = key.split(',');
        const [toState, writeSym, dir] = currentMachine.transitions[key];
        const displayLabel = `${readSym}/${writeSym}${dir}`;
        
        elements.push({
            data: {
                id: `${key}->${toState}`,
                source: fromState,
                target: toState,
                label: displayLabel
            }
        });
    });

    cy = cytoscape({
        container: document.getElementById('cy'),
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#4f46e5',
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-valign': 'center',
                    'font-size': '16px',
                    'font-weight': 'bold',
                    'width': '60px',
                    'height': '60px',
                    'border-width': 2,
                    'border-color': '#312e81'
                }
            },
            {
                selector: '.start-node',
                style: {
                    'visibility': 'hidden',
                    'width': '1px',
                    'height': '1px'
                }
            },
            {
                selector: '.accept-state',
                style: {
                    'border-width': 6,
                    'border-style': 'double',
                    'border-color': '#22c55e',
                    'background-color': '#064e3b'
                }
            },
            {
                selector: 'node.active',
                style: {
                    'background-color': '#06b6d4',
                    'border-color': '#fff',
                    'box-shadow': '0 0 25px #06b6d4',
                    'scale': 1.1
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#6366f1',
                    'target-arrow-color': '#6366f1',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '14px',
                    'font-family': 'monospace',
                    'color': '#a5b4fc',
                    'text-background-opacity': 0.9,
                    'text-background-color': '#020617',
                    'text-background-padding': '3px',
                    'text-rotation': 'autorotate',
                    'arrow-scale': 1.5
                }
            },
            {
                selector: 'edge[id="init-arrow"]',
                style: {
                    'label': '',
                    'width': 2,
                    'line-color': '#94a3b8'
                }
            },
            {
              selector: 'edge[source = target]',
              style: {
                'loop-direction': '-45deg',
                'loop-sweep': '90deg',
                'control-point-step-size': 70
              }
            }
        ],
        layout: { name: 'preset' },
        userZoomingEnabled: true,
        userPanningEnabled: true
    });
}

// --- Transition Table ---
function renderTable() {
    // Dynamically discover ALL symbols from the current machine's transitions
    const symbolSet = new Set();
    Object.keys(currentMachine.transitions).forEach(k => {
        symbolSet.add(k.split(',')[1]); // read symbols
        symbolSet.add(currentMachine.transitions[k][1]); // write symbols
    });
    // Always include blank
    symbolSet.add('_');
    const symbols = Array.from(symbolSet);

    // Detect accept states dynamically
    const states = currentMachine.states;
    const acceptStates = states.filter(s => 
        s.includes('accept') || s.includes('final') || 
        s === states[states.length - 1]
    );

    const head = document.getElementById('table-head');
    head.innerHTML = '<th class="px-6 py-4 border-b border-white/10">State</th>';
    symbols.forEach(s => {
        head.innerHTML += `<th class="px-6 py-4 border-b border-white/10 text-center">${s}</th>`;
    });

    const body = document.getElementById('table-body');
    body.innerHTML = '';
    states.forEach((state, idx) => {
        const isInitial = idx === 0;
        const isFinal = acceptStates.includes(state);
        
        let stateDisplay = state;
        if (isInitial) stateDisplay = '→ ' + state;
        if (isFinal) stateDisplay = '* ' + state;

        let row = `<tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
            <td class="px-6 py-4 font-bold ${isInitial ? 'text-accent' : (isFinal ? 'text-emerald-400' : 'text-gray-400')}">${stateDisplay}</td>`;
        
        symbols.forEach(sym => {
            const trans = currentMachine.transitions[`${state},${sym}`];
            const content = trans ? `(${trans[0]}, ${trans[1]}, ${trans[2]})` : '—';
            row += `<td class="px-6 py-4 text-center cursor-pointer hover:bg-accent/10 font-mono text-xs">${content}</td>`;
        });
        
        row += '</tr>';
        body.innerHTML += row;
    });
}

// --- AI Chat Logic ---
const TM_FORMULA_INFO = `
A Turing Machine (TM) is defined by a 7-tuple: M = (Q, Σ, Γ, δ, q0, B, F)
• Q: Finite set of states
• Σ: Input alphabet
• Γ: Tape alphabet
• δ: Transition function
• q0: Initial state
• B: Blank symbol (_)
• F: Final (accept) states
`;

async function handleChatInput() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim().toLowerCase();
    if (!text) return;

    addChatMessage(text, 'user');
    input.value = '';
    
    document.getElementById('chat-loading').classList.remove('hidden');

    // Simulate AI thinking and response
    setTimeout(() => {
        document.getElementById('chat-loading').classList.add('hidden');
        
        if (text.includes('formula') || text.includes('concept') || text.includes('tuple')) {
            addChatMessage("The formula for a Turing Machine is a 7-tuple: M = (Q, \u03a3, \u0393, \u03b4, q0, B, F).", 'ai');
            addChatMessage(TM_FORMULA_INFO, 'ai');
        } else if (text.includes('binary') || text.includes('number') || text.includes('math')) {
            loadRandomQuestion('binary_increment');
        } else if (text.includes('question') || text.includes('ask') || text.includes('challenge') || text.includes('next') || text.includes('random')) {
            loadRandomQuestion();
        } else if (text.includes('easy')) {
            loadRandomQuestion('', 'easy');
        } else if (text.includes('hard')) {
            loadRandomQuestion('', 'hard');
        } else if (text.includes('palindrome')) {
            loadRandomQuestion('palindrome');
        } else if (text.includes('parity') || text.includes('even') || text.includes('odd')) {
            loadRandomQuestion('even_ones');
        } else if (text.includes('accept') || text.includes('status')) {
             addChatMessage(`Status check: String "${currentMachine.input}" is currently ${currentMachine.status}.`, 'ai');
        } else {
             // Fallback to backend AI generation
             callBackendAI(text);
        }
    }, 800);
}

// Load a random question from the 1050+ database
async function loadRandomQuestion(type = '', difficulty = '') {
    try {
        let url = `${API_BASE}/questions/random?`;
        if (type) url += `type=${type}&`;
        if (difficulty) url += `difficulty=${difficulty}&`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            addChatMessage("Could not load question from database.", 'ai');
            return;
        }
        
        // Load the machine with its UNIQUE transitions
        currentMachine = { ...data.machine, status: 'RUNNING', stepCount: 0 };
        document.getElementById('input-string').value = currentMachine.input;
        initTape();
        initGraph();
        updateUI();
        
        addChatMessage(`[Q#${data.id}] ${data.title}`, 'ai');
        addChatMessage(data.description, 'ai');
        addChatMessage(`Difficulty: ${data.difficulty.toUpperCase()} | Expected: ${data.expected_result}`, 'ai');
        addChatMessage("The transition table and state diagram have been updated for THIS question. Click PLAY to simulate!", 'ai');
    } catch (err) {
        addChatMessage("Database not available. Try selecting from the dropdown menu.", 'ai');
    }
}

async function callBackendAI(prompt) {
    try {
        const response = await fetch(`${API_BASE}/ai-generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await response.json();
        
        addChatMessage(data.explanation, 'ai');
        if (data.machine) {
            currentMachine = { ...data.machine, status: 'RUNNING', stepCount: 0 };
            document.getElementById('input-string').value = currentMachine.input;
            initTape();
            initGraph();
            updateUI();
            addChatMessage("Machine configured. Try running it!", 'ai');
        }
    } catch (err) {
        addChatMessage("I'm having trouble connecting to the logic core.", 'ai');
    }
}

function addChatMessage(text, role) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chatbot-msg ${role}`;
    div.innerText = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

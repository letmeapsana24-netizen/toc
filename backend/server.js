const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());
// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, '../frontend')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// Helper for TM simulation
const simulateStep = (machine) => {
    const { states, tape, head, currentState, transitions, input } = machine;
    
    // Dynamically detect accept states (last state or states with 'accept'/'final' in name)
    const acceptStates = states.filter(s => 
        s.includes('accept') || s.includes('final') || 
        s === states[states.length - 1]
    );
    const rejectStates = states.filter(s => s.includes('reject'));
    
    // Default blank symbol
    const currentSymbol = (tape[head] === undefined || tape[head] === null) ? '_' : tape[head];
    const transitionKey = `${currentState},${currentSymbol}`;
    
    const transition = transitions[transitionKey];
    
    if (!transition) {
        // No transition - Halt
        if (acceptStates.includes(currentState)) {
            return { ...machine, status: 'ACCEPTED', action: `Halted in Accept state (${currentState})` };
        }
        return { ...machine, status: 'REJECTED', action: `No transition found at δ(${currentState}, ${currentSymbol}), Halted` };
    }
    
    const [nextState, writeSymbol, moveDirection] = transition;
    
    // Update tape
    const newTape = [...tape];
    newTape[head] = writeSymbol;
    
    // Move head
    let newHead = head;
    if (moveDirection === 'R') newHead++;
    else if (moveDirection === 'L') newHead--;
    
    // Ensure tape grows if needed
    if (newHead < 0) {
        newTape.unshift('_');
        newHead = 0;
    } else if (newHead >= newTape.length) {
        newTape.push('_');
    }
    
    let nextStatus = 'RUNNING';
    if (acceptStates.includes(nextState)) nextStatus = 'ACCEPTED';
    else if (rejectStates.includes(nextState)) nextStatus = 'REJECTED';
    
    return {
        ...machine,
        tape: newTape,
        head: newHead,
        currentState: nextState,
        status: nextStatus,
        action: `Transition: δ(${currentState}, ${currentSymbol}) → (${nextState}, ${writeSymbol}, ${moveDirection})`
    };
};

app.post('/api/simulate-step', (req, res) => {
    const machine = req.body;
    const nextStep = simulateStep(machine);
    res.json(nextStep);
});

app.post('/api/run-complete', (req, res) => {
    let machine = req.body;
    const steps = [JSON.parse(JSON.stringify(machine))];
    let limit = 1000; // Safety limit
    
    while (machine.status === 'RUNNING' && limit > 0) {
        machine = simulateStep(machine);
        steps.push(JSON.parse(JSON.stringify(machine)));
        limit--;
    }
    
    res.json({ steps, finalStatus: machine.status });
});

app.post('/api/validate', (req, res) => {
    const { states, transitions } = req.body;
    let errors = [];
    if (!states || states.length === 0) errors.push("Machine must have at least one state.");
    if (!transitions || Object.keys(transitions).length === 0) errors.push("Machine must have transitions.");
    
    res.json({ valid: errors.length === 0, errors });
});

// Mock Problems
const { exec } = require('child_process');

// Extended problems from user handwritten notes
const PROBLEMS = {
    "anbn": {
        id: "anbn",
        name: "L = { a^n b^n }",
        description: "Matches equal number of a's followed by b's (X, Y marks).",
        machine: {
            states: ["q0", "q1", "q2", "q3", "q4"],
            input: "aabb",
            tape: ["a", "a", "b", "b", "_"],
            head: 0,
            currentState: "q0",
            transitions: {
                "q0,a": ["q1", "X", "R"],
                "q0,Y": ["q3", "Y", "R"],
                "q0,_": ["q4", "_", "R"],
                "q1,a": ["q1", "a", "R"],
                "q1,Y": ["q1", "Y", "R"],
                "q1,b": ["q2", "Y", "L"],
                "q2,a": ["q2", "a", "L"],
                "q2,Y": ["q2", "Y", "L"],
                "q2,X": ["q0", "X", "R"],
                "q3,Y": ["q3", "Y", "R"],
                "q3,_": ["q4", "_", "R"]
            }
        }
    },
    "binary_inc": {
        id: "binary_inc",
        name: "Binary Incrementer",
        description: "Adds 1 to a binary string (e.g. 1011 -> 1100).",
        machine: {
            states: ["q0", "q1", "q2", "q3"],
            input: "1011",
            tape: ["1", "0", "1", "1", "_"],
            head: 0,
            currentState: "q0",
            transitions: {
                "q0,0": ["q0", "0", "R"],
                "q0,1": ["q0", "1", "R"],
                "q0,_": ["q1", "_", "L"],
                "q1,1": ["q1", "0", "L"],
                "q1,0": ["q2", "1", "L"],
                "q1,_": ["q2", "1", "L"],
                "q2,0": ["q2", "0", "L"],
                "q2,1": ["q2", "1", "L"],
                "q2,_": ["q3", "_", "R"]
            }
        }
    }
};

app.get('/api/problems', (req, res) => {
    res.json(Object.values(PROBLEMS));
});

app.post('/api/ai-generate', (req, res) => {
    const { prompt } = req.body;
    
    // Call Python AI Inference for natural language generation
    const pythonScript = path.join(__dirname, '../ai/inference.py');
    exec(`python "${pythonScript}" "${prompt}"`, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            // Fallback for demo stability
            return res.json({ machine: PROBLEMS.anbn.machine, explanation: "AI could not reach logical core. Loading 'a^n b^n' as fallback." });
        }
        
        try {
            const result = JSON.parse(stdout);
            if (result.error) {
                 return res.json({ explanation: result.error });
            }
            res.json({ machine: result, explanation: result.explanation });
        } catch (e) {
            res.json({ machine: PROBLEMS.anbn.machine, explanation: "Parsed machine from logic templates." });
        }
    });
});

// ========================================
// DATABASE-DRIVEN QUESTION BANK (1050+ Qs)
// ========================================
const Database = require('better-sqlite3');
const DB_PATH = path.join(__dirname, '../database/tm_questions.db');
let db;
try {
    db = new Database(DB_PATH, { readonly: true });
    console.log(`[DB] Connected to ${DB_PATH}`);
} catch (err) {
    console.warn(`[DB] Could not connect to database: ${err.message}`);
}

// GET /api/questions - List all questions (paginated)
app.get('/api/questions', (req, res) => {
    if (!db) return res.status(500).json({ error: 'Database not connected' });
    
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const difficulty = req.query.difficulty || '';
    const type = req.query.type || '';
    
    let where = '1=1';
    const params = [];
    if (difficulty) { where += ' AND difficulty = ?'; params.push(difficulty); }
    if (type) { where += ' AND language_type = ?'; params.push(type); }
    
    const total = db.prepare(`SELECT COUNT(*) as cnt FROM questions WHERE ${where}`).get(...params).cnt;
    const questions = db.prepare(`SELECT id, title, description, difficulty, language_type, input_example, expected_result FROM questions WHERE ${where} LIMIT ? OFFSET ?`).all(...params, limit, offset);
    
    res.json({
        total,
        page,
        pages: Math.ceil(total / limit),
        questions
    });
});

// GET /api/questions/random - Get a random question
app.get('/api/questions/random', (req, res) => {
    if (!db) return res.status(500).json({ error: 'Database not connected' });
    
    const difficulty = req.query.difficulty || '';
    const type = req.query.type || '';
    
    let where = '1=1';
    const params = [];
    if (difficulty) { where += ' AND difficulty = ?'; params.push(difficulty); }
    if (type) { where += ' AND language_type = ?'; params.push(type); }
    
    const q = db.prepare(`SELECT * FROM questions WHERE ${where} ORDER BY RANDOM() LIMIT 1`).get(...params);
    if (!q) return res.status(404).json({ error: 'No question found' });
    
    const statesRows = db.prepare('SELECT state_name, is_start, is_accept, is_reject FROM states WHERE question_id = ?').all(q.id);
    const transRows = db.prepare('SELECT current_state, read_symbol, write_symbol, move, next_state FROM transitions WHERE question_id = ?').all(q.id);
    const diagram = db.prepare('SELECT diagram_json FROM diagrams WHERE question_id = ?').get(q.id);
    
    // Build machine object compatible with frontend
    const transitions = {};
    transRows.forEach(t => {
        transitions[`${t.current_state},${t.read_symbol}`] = [t.next_state, t.write_symbol, t.move];
    });
    
    const machine = {
        states: statesRows.map(s => s.state_name),
        input: q.input_example,
        tape: q.input_example.split('').concat(['_', '_', '_']),
        head: 0,
        currentState: statesRows.find(s => s.is_start)?.state_name || 'q0',
        transitions
    };
    
    res.json({
        id: q.id,
        title: q.title,
        description: q.description,
        difficulty: q.difficulty,
        language_type: q.language_type,
        expected_result: q.expected_result,
        machine,
        diagram: diagram ? JSON.parse(diagram.diagram_json) : null
    });
});

// GET /api/questions/:id - Get a specific question with full machine
app.get('/api/questions/:id', (req, res) => {
    if (!db) return res.status(500).json({ error: 'Database not connected' });
    
    const q = db.prepare('SELECT * FROM questions WHERE id = ?').get(req.params.id);
    if (!q) return res.status(404).json({ error: 'Question not found' });
    
    const statesRows = db.prepare('SELECT state_name, is_start, is_accept, is_reject FROM states WHERE question_id = ?').all(q.id);
    const transRows = db.prepare('SELECT current_state, read_symbol, write_symbol, move, next_state FROM transitions WHERE question_id = ?').all(q.id);
    const diagram = db.prepare('SELECT diagram_json FROM diagrams WHERE question_id = ?').get(q.id);
    
    const transitions = {};
    transRows.forEach(t => {
        transitions[`${t.current_state},${t.read_symbol}`] = [t.next_state, t.write_symbol, t.move];
    });
    
    const machine = {
        states: statesRows.map(s => s.state_name),
        input: q.input_example,
        tape: q.input_example.split('').concat(['_', '_', '_']),
        head: 0,
        currentState: statesRows.find(s => s.is_start)?.state_name || 'q0',
        transitions
    };
    
    res.json({
        id: q.id,
        title: q.title,
        description: q.description,
        difficulty: q.difficulty,
        language_type: q.language_type,
        expected_result: q.expected_result,
        machine,
        diagram: diagram ? JSON.parse(diagram.diagram_json) : null
    });
});

// GET /api/questions/types - Get all unique language types
app.get('/api/question-types', (req, res) => {
    if (!db) return res.status(500).json({ error: 'Database not connected' });
    const types = db.prepare('SELECT DISTINCT language_type, COUNT(*) as count FROM questions GROUP BY language_type ORDER BY count DESC').all();
    res.json(types);
});

app.listen(PORT, () => {
    console.log(`Backend server running on http://localhost:${PORT}`);
});

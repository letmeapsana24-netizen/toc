import sqlite3
import json
import random
import os

# Connect to SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database', 'tm_questions.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ========================================
# 1. CREATE TABLES (3NF Normalized Schema)
# ========================================
cursor.executescript('''
DROP TABLE IF EXISTS diagrams;
DROP TABLE IF EXISTS transitions;
DROP TABLE IF EXISTS states;
DROP TABLE IF EXISTS questions;

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    difficulty TEXT CHECK(difficulty IN ('easy','medium','hard')),
    language_type TEXT,
    input_example TEXT,
    expected_result TEXT CHECK(expected_result IN ('ACCEPT','REJECT')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    state_name TEXT,
    is_start INTEGER DEFAULT 0,
    is_accept INTEGER DEFAULT 0,
    is_reject INTEGER DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    current_state TEXT,
    read_symbol TEXT,
    write_symbol TEXT,
    move TEXT CHECK(move IN ('L','R','S')),
    next_state TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE diagrams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    diagram_json TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
''')

print("[OK] Tables created successfully.")

# ========================================
# 2. TURING MACHINE TEMPLATES (Core Logic)
# ========================================

def tm_anbn(n, alphabet=('a','b')):
    """L = {a^n b^n} - Equal count matching"""
    a, b = alphabet
    input_str = a * n + b * n
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q2", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q3", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q4", "is_start": 0, "is_accept": 1, "is_reject": 0},
    ]
    trans = [
        ("q0", a, "X", "R", "q1"), ("q0", "Y", "Y", "R", "q3"), ("q0", "_", "_", "R", "q4"),
        ("q1", a, a, "R", "q1"), ("q1", "Y", "Y", "R", "q1"), ("q1", b, "Y", "L", "q2"),
        ("q2", a, a, "L", "q2"), ("q2", "Y", "Y", "L", "q2"), ("q2", "X", "X", "R", "q0"),
        ("q3", "Y", "Y", "R", "q3"), ("q3", "_", "_", "R", "q4"),
    ]
    return input_str, states_list, trans

def tm_0n1n(n):
    """L = {0^n 1^n} - Binary version of anbn"""
    input_str = "0" * n + "1" * n
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q2", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q3", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q4", "is_start": 0, "is_accept": 1, "is_reject": 0},
    ]
    trans = [
        ("q0", "0", "X", "R", "q1"), ("q0", "Y", "Y", "R", "q3"), ("q0", "_", "_", "R", "q4"),
        ("q1", "0", "0", "R", "q1"), ("q1", "Y", "Y", "R", "q1"), ("q1", "1", "Y", "L", "q2"),
        ("q2", "0", "0", "L", "q2"), ("q2", "Y", "Y", "L", "q2"), ("q2", "X", "X", "R", "q0"),
        ("q3", "Y", "Y", "R", "q3"), ("q3", "_", "_", "R", "q4"),
    ]
    return input_str, states_list, trans

def tm_even_ones(bits):
    """Even number of 1s in a binary string"""
    input_str = bits
    count_ones = bits.count('1')
    states_list = [
        {"name": "q_even", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q_odd", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    trans = [
        ("q_even", "0", "0", "R", "q_even"), ("q_even", "1", "1", "R", "q_odd"),
        ("q_even", "_", "_", "S", "q_accept"),
        ("q_odd", "0", "0", "R", "q_odd"), ("q_odd", "1", "1", "R", "q_even"),
        ("q_odd", "_", "_", "S", "q_reject"),
    ]
    expected = "ACCEPT" if count_ones % 2 == 0 else "REJECT"
    return input_str, states_list, trans, expected

def tm_odd_ones(bits):
    """Odd number of 1s in a binary string"""
    input_str = bits
    count_ones = bits.count('1')
    states_list = [
        {"name": "q_even", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q_odd", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    trans = [
        ("q_even", "0", "0", "R", "q_even"), ("q_even", "1", "1", "R", "q_odd"),
        ("q_even", "_", "_", "S", "q_reject"),
        ("q_odd", "0", "0", "R", "q_odd"), ("q_odd", "1", "1", "R", "q_even"),
        ("q_odd", "_", "_", "S", "q_accept"),
    ]
    expected = "ACCEPT" if count_ones % 2 == 1 else "REJECT"
    return input_str, states_list, trans, expected

def tm_even_zeros(bits):
    """Even number of 0s in a binary string"""
    input_str = bits
    count_zeros = bits.count('0')
    states_list = [
        {"name": "q_even", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q_odd", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    trans = [
        ("q_even", "1", "1", "R", "q_even"), ("q_even", "0", "0", "R", "q_odd"),
        ("q_even", "_", "_", "S", "q_accept"),
        ("q_odd", "1", "1", "R", "q_odd"), ("q_odd", "0", "0", "R", "q_even"),
        ("q_odd", "_", "_", "S", "q_reject"),
    ]
    expected = "ACCEPT" if count_zeros % 2 == 0 else "REJECT"
    return input_str, states_list, trans, expected

def tm_binary_increment(bits):
    """Binary Incrementer: adds 1 to binary number"""
    input_str = bits
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q2", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q3", "is_start": 0, "is_accept": 1, "is_reject": 0},
    ]
    trans = [
        ("q0", "0", "0", "R", "q0"), ("q0", "1", "1", "R", "q0"), ("q0", "_", "_", "L", "q1"),
        ("q1", "1", "0", "L", "q1"), ("q1", "0", "1", "L", "q2"), ("q1", "_", "1", "L", "q2"),
        ("q2", "0", "0", "L", "q2"), ("q2", "1", "1", "L", "q2"), ("q2", "_", "_", "R", "q3"),
    ]
    return input_str, states_list, trans

def tm_starts_with(symbol, input_str):
    """Accept strings that start with a specific symbol"""
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    other = '1' if symbol == '0' else '0'
    trans = [
        ("q0", symbol, symbol, "R", "q_accept"),
        ("q0", other, other, "R", "q_reject"),
        ("q0", "_", "_", "S", "q_reject"),
    ]
    expected = "ACCEPT" if input_str and input_str[0] == symbol else "REJECT"
    return input_str, states_list, trans, expected

def tm_ends_with(symbol, input_str):
    """Accept strings that end with a specific symbol"""
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    other = '1' if symbol == '0' else '0'
    trans = [
        ("q0", "0", "0", "R", "q0"), ("q0", "1", "1", "R", "q0"), ("q0", "_", "_", "L", "q1"),
        ("q1", symbol, symbol, "S", "q_accept"), ("q1", other, other, "S", "q_reject"),
        ("q1", "_", "_", "S", "q_reject"),
    ]
    expected = "ACCEPT" if input_str and input_str[-1] == symbol else "REJECT"
    return input_str, states_list, trans, expected

def tm_all_same(symbol, input_str):
    """Accept strings that contain ONLY the given symbol"""
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    other = '1' if symbol == '0' else '0'
    trans = [
        ("q0", symbol, symbol, "R", "q0"),
        ("q0", other, other, "R", "q_reject"),
        ("q0", "_", "_", "S", "q_accept"),
    ]
    expected = "ACCEPT" if all(c == symbol for c in input_str) else "REJECT"
    return input_str, states_list, trans, expected

def tm_contains(symbol, input_str):
    """Accept strings that contain at least one of the given symbol"""
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
        {"name": "q_reject", "is_start": 0, "is_accept": 0, "is_reject": 1},
    ]
    other = '1' if symbol == '0' else '0'
    trans = [
        ("q0", symbol, symbol, "R", "q_accept"),
        ("q0", other, other, "R", "q0"),
        ("q0", "_", "_", "S", "q_reject"),
    ]
    expected = "ACCEPT" if symbol in input_str else "REJECT"
    return input_str, states_list, trans, expected

def tm_palindrome_ab(input_str):
    """Palindrome checker for {a, b}"""
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q2", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q3", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q4", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q5", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
    ]
    trans = [
        ("q0", "a", "_", "R", "q1"), ("q0", "b", "_", "R", "q2"), ("q0", "_", "_", "R", "q_accept"),
        ("q1", "a", "a", "R", "q1"), ("q1", "b", "b", "R", "q1"), ("q1", "_", "_", "L", "q3"),
        ("q2", "a", "a", "R", "q2"), ("q2", "b", "b", "R", "q2"), ("q2", "_", "_", "L", "q4"),
        ("q3", "a", "_", "L", "q5"), ("q3", "_", "_", "R", "q_accept"),
        ("q4", "b", "_", "L", "q5"), ("q4", "_", "_", "R", "q_accept"),
        ("q5", "a", "a", "L", "q5"), ("q5", "b", "b", "L", "q5"), ("q5", "_", "_", "R", "q0"),
    ]
    expected = "ACCEPT" if input_str == input_str[::-1] else "REJECT"
    return input_str, states_list, trans, expected

def tm_anbncn(n):
    """L = {a^n b^n c^n} - Context Sensitive"""
    input_str = "a" * n + "b" * n + "c" * n
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q2", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q3", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q4", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q5", "is_start": 0, "is_accept": 1, "is_reject": 0},
    ]
    trans = [
        ("q0", "a", "X", "R", "q1"), ("q0", "Y", "Y", "R", "q4"),
        ("q1", "a", "a", "R", "q1"), ("q1", "Y", "Y", "R", "q1"), ("q1", "b", "Y", "R", "q2"),
        ("q2", "b", "b", "R", "q2"), ("q2", "Z", "Z", "R", "q2"), ("q2", "c", "Z", "L", "q3"),
        ("q3", "Z", "Z", "L", "q3"), ("q3", "b", "b", "L", "q3"), ("q3", "Y", "Y", "L", "q3"),
        ("q3", "a", "a", "L", "q3"), ("q3", "X", "X", "R", "q0"),
        ("q4", "Y", "Y", "R", "q4"), ("q4", "Z", "Z", "R", "q4"), ("q4", "_", "_", "R", "q5"),
    ]
    return input_str, states_list, trans

def tm_ww_reverse(input_str):
    """Accept strings of form w#w^R (word, hash, reverse)"""
    states_list = [
        {"name": "q0", "is_start": 1, "is_accept": 0, "is_reject": 0},
        {"name": "q1", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q2", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q3", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q4", "is_start": 0, "is_accept": 0, "is_reject": 0},
        {"name": "q_accept", "is_start": 0, "is_accept": 1, "is_reject": 0},
    ]
    trans = [
        ("q0", "0", "X", "R", "q1"), ("q0", "1", "X", "R", "q2"), ("q0", "#", "#", "R", "q4"),
        ("q1", "0", "0", "R", "q1"), ("q1", "1", "1", "R", "q1"), ("q1", "#", "#", "R", "q3"),
        ("q2", "0", "0", "R", "q2"), ("q2", "1", "1", "R", "q2"), ("q2", "#", "#", "R", "q3"),
        ("q3", "X", "X", "R", "q3"), ("q3", "0", "X", "L", "q0"), ("q3", "1", "X", "L", "q0"),
        ("q4", "X", "X", "R", "q4"), ("q4", "_", "_", "S", "q_accept"),
    ]
    return input_str, states_list, trans

# ========================================
# 3. GENERATE 1000+ UNIQUE QUESTIONS
# ========================================

question_id = 0

def insert_question(title, desc, diff, lang_type, input_str, expected, states_list, transitions_list):
    global question_id
    cursor.execute(
        "INSERT INTO questions (title, description, difficulty, language_type, input_example, expected_result) VALUES (?,?,?,?,?,?)",
        (title, desc, diff, lang_type, input_str, expected)
    )
    qid = cursor.lastrowid
    question_id = qid
    
    # Insert states
    for s in states_list:
        cursor.execute(
            "INSERT INTO states (question_id, state_name, is_start, is_accept, is_reject) VALUES (?,?,?,?,?)",
            (qid, s['name'], s['is_start'], s['is_accept'], s['is_reject'])
        )
    
    # Insert transitions
    for t in transitions_list:
        cursor.execute(
            "INSERT INTO transitions (question_id, current_state, read_symbol, write_symbol, move, next_state) VALUES (?,?,?,?,?,?)",
            (qid, t[0], t[1], t[2], t[3], t[4])
        )
    
    # Insert diagram as JSON
    diagram = {
        "states": [s['name'] for s in states_list],
        "transitions": [
            {"from": t[0], "read": t[1], "write": t[2], "move": t[3], "to": t[4]}
            for t in transitions_list
        ]
    }
    cursor.execute(
        "INSERT INTO diagrams (question_id, diagram_json) VALUES (?,?)",
        (qid, json.dumps(diagram))
    )
    return qid

print("[...] Generating 1000+ unique questions...")

# --- Category 1: a^n b^n (100 questions) ---
for n in range(1, 51):
    inp, st, tr = tm_anbn(n, ('a', 'b'))
    insert_question(
        f"Q: Accept a^{n}b^{n}", 
        f"Design TM for L={{a^n b^n}} where n={n}. Input: '{inp}'. Should ACCEPT.",
        "easy" if n <= 5 else ("medium" if n <= 15 else "hard"),
        "anbn", inp, "ACCEPT", st, tr
    )

for n in range(1, 51):
    # Rejection cases: mismatched counts
    m = random.choice([i for i in range(1, 20) if i != n])
    inp = 'a' * n + 'b' * m
    _, st, tr = tm_anbn(max(n, m), ('a', 'b'))
    insert_question(
        f"Q: Reject a^{n}b^{m}",
        f"Design TM for L={{a^n b^n}}. Input: '{inp}'. Should REJECT (unequal counts).",
        "easy" if n <= 5 else "medium",
        "anbn_reject", inp, "REJECT", st, tr
    )

# --- Category 2: 0^n 1^n (100 questions) ---
for n in range(1, 51):
    inp, st, tr = tm_0n1n(n)
    insert_question(
        f"Q: Accept 0^{n}1^{n}",
        f"Design TM for L={{0^n 1^n}} where n={n}. Input: '{inp}'. Should ACCEPT.",
        "easy" if n <= 5 else ("medium" if n <= 15 else "hard"),
        "0n1n", inp, "ACCEPT", st, tr
    )

for n in range(1, 51):
    m = random.choice([i for i in range(1, 20) if i != n])
    inp = '0' * n + '1' * m
    _, st, tr = tm_0n1n(max(n, m))
    insert_question(
        f"Q: Reject 0^{n}1^{m}",
        f"Design TM for L={{0^n 1^n}}. Input: '{inp}'. Should REJECT.",
        "easy" if n <= 5 else "medium",
        "0n1n_reject", inp, "REJECT", st, tr
    )

# --- Category 3: Even/Odd 1s (200 questions) ---
for i in range(100):
    length = random.randint(2, 12)
    bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_even_ones(bits)
    insert_question(
        f"Q: Even 1s in '{bits}'?",
        f"Design TM to accept binary strings with even number of 1s. Input: '{bits}'. Count of 1s = {bits.count('1')}.",
        "easy", "even_ones", inp, expected, st, tr
    )

for i in range(100):
    length = random.randint(2, 12)
    bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_odd_ones(bits)
    insert_question(
        f"Q: Odd 1s in '{bits}'?",
        f"Design TM to accept binary strings with odd number of 1s. Input: '{bits}'. Count of 1s = {bits.count('1')}.",
        "easy", "odd_ones", inp, expected, st, tr
    )

# --- Category 4: Even/Odd 0s (100 questions) ---
for i in range(100):
    length = random.randint(2, 12)
    bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_even_zeros(bits)
    insert_question(
        f"Q: Even 0s in '{bits}'?",
        f"Design TM to accept binary strings with even number of 0s. Input: '{bits}'. Count of 0s = {bits.count('0')}.",
        "easy", "even_zeros", inp, expected, st, tr
    )

# --- Category 5: Binary Increment (50 questions) ---
for i in range(50):
    length = random.randint(2, 8)
    bits = ''.join(random.choice('01') for _ in range(length))
    if bits[0] == '0' and len(bits) > 1:
        bits = '1' + bits[1:]
    inp, st, tr = tm_binary_increment(bits)
    result_int = int(bits, 2) + 1
    result_bin = bin(result_int)[2:]
    insert_question(
        f"Q: Increment '{bits}' (={int(bits,2)})",
        f"Design TM to add 1 to binary number '{bits}' (decimal {int(bits,2)}). Expected result: '{result_bin}' (decimal {result_int}).",
        "medium", "binary_increment", inp, "ACCEPT", st, tr
    )

# --- Category 6: Starts With / Ends With (100 questions) ---
for i in range(50):
    length = random.randint(2, 8)
    bits = ''.join(random.choice('01') for _ in range(length))
    symbol = random.choice(['0', '1'])
    inp, st, tr, expected = tm_starts_with(symbol, bits)
    insert_question(
        f"Q: Does '{bits}' start with '{symbol}'?",
        f"Design TM to accept strings starting with '{symbol}'. Input: '{bits}'.",
        "easy", f"starts_with_{symbol}", inp, expected, st, tr
    )

for i in range(50):
    length = random.randint(2, 8)
    bits = ''.join(random.choice('01') for _ in range(length))
    symbol = random.choice(['0', '1'])
    inp, st, tr, expected = tm_ends_with(symbol, bits)
    insert_question(
        f"Q: Does '{bits}' end with '{symbol}'?",
        f"Design TM to accept strings ending with '{symbol}'. Input: '{bits}'.",
        "easy", f"ends_with_{symbol}", inp, expected, st, tr
    )

# --- Category 7: All Same Symbol (50 questions) ---
for i in range(50):
    symbol = random.choice(['0', '1'])
    if random.random() > 0.5:
        bits = symbol * random.randint(2, 8)  # All same (ACCEPT)
    else:
        length = random.randint(2, 8)
        bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_all_same(symbol, bits)
    insert_question(
        f"Q: Is '{bits}' all {symbol}s?",
        f"Design TM to accept strings containing only '{symbol}'. Input: '{bits}'.",
        "easy", f"all_{symbol}s", inp, expected, st, tr
    )

# --- Category 8: Contains Symbol (50 questions) ---
for i in range(50):
    symbol = random.choice(['0', '1'])
    length = random.randint(2, 8)
    bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_contains(symbol, bits)
    insert_question(
        f"Q: Does '{bits}' contain a '{symbol}'?",
        f"Design TM to accept strings containing at least one '{symbol}'. Input: '{bits}'.",
        "easy", f"contains_{symbol}", inp, expected, st, tr
    )

# --- Category 9: Palindromes {a,b} (100 questions) ---
for i in range(50):
    half_len = random.randint(1, 4)
    half = ''.join(random.choice('ab') for _ in range(half_len))
    inp = half + random.choice(['', 'a', 'b']) + half[::-1]  # Palindrome
    _, st, tr, expected = tm_palindrome_ab(inp)
    insert_question(
        f"Q: Is '{inp}' a palindrome?",
        f"Design TM for palindrome checker over {{a,b}}. Input: '{inp}'.",
        "medium", "palindrome", inp, expected, st, tr
    )

for i in range(50):
    length = random.randint(2, 6)
    inp = ''.join(random.choice('ab') for _ in range(length))
    _, st, tr, expected = tm_palindrome_ab(inp)
    insert_question(
        f"Q: Is '{inp}' a palindrome?",
        f"Design TM for palindrome checker over {{a,b}}. Input: '{inp}'.",
        "medium", "palindrome", inp, expected, st, tr
    )

# --- Category 10: a^n b^n c^n (50 questions) ---
for n in range(1, 26):
    inp, st, tr = tm_anbncn(n)
    insert_question(
        f"Q: Accept a^{n}b^{n}c^{n}",
        f"Design TM for L={{a^n b^n c^n}} where n={n}. Input: '{inp}'.",
        "hard", "anbncn", inp, "ACCEPT", st, tr
    )

for n in range(1, 26):
    # Rejection: mismatched
    a_count = n
    b_count = random.choice([i for i in range(1, 10) if i != n])
    c_count = n
    inp = 'a' * a_count + 'b' * b_count + 'c' * c_count
    _, st, tr = tm_anbncn(max(a_count, b_count, c_count))
    insert_question(
        f"Q: Reject a^{a_count}b^{b_count}c^{c_count}",
        f"Design TM for L={{a^n b^n c^n}}. Input: '{inp}'. Should REJECT.",
        "hard", "anbncn_reject", inp, "REJECT", st, tr
    )

# --- Category 11: More Even 0s (50 questions) ---
for i in range(50):
    length = random.randint(3, 10)
    bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_even_zeros(bits)
    insert_question(
        f"Q: Even 0s check '{bits}'",
        f"Binary parity check on 0s. Input: '{bits}'. Count of 0s = {bits.count('0')}.",
        "easy", "even_zeros", inp, expected, st, tr
    )

# --- Category 12: More Starts With (50 questions) ---
for i in range(50):
    length = random.randint(3, 10)
    bits = ''.join(random.choice('01') for _ in range(length))
    symbol = random.choice(['0', '1'])
    inp, st, tr, expected = tm_starts_with(symbol, bits)
    insert_question(
        f"Q: Starts with '{symbol}'? Input: '{bits}'",
        f"Check if binary string starts with '{symbol}'. Input: '{bits}'.",
        "easy", f"starts_with_{symbol}", inp, expected, st, tr
    )

# --- Category 13: More Contains (50 questions) ---
for i in range(50):
    symbol = random.choice(['0', '1'])
    length = random.randint(3, 10)
    bits = ''.join(random.choice('01') for _ in range(length))
    inp, st, tr, expected = tm_contains(symbol, bits)
    insert_question(
        f"Q: Contains '{symbol}'? Input: '{bits}'",
        f"Accept if string contains at least one '{symbol}'. Input: '{bits}'.",
        "easy", f"contains_{symbol}", inp, expected, st, tr
    )

conn.commit()

# ========================================
# 4. VERIFY
# ========================================
cursor.execute("SELECT COUNT(*) FROM questions")
total = cursor.fetchone()[0]
print(f"[OK] Total questions generated: {total}")

cursor.execute("SELECT COUNT(*) FROM states")
total_states = cursor.fetchone()[0]
print(f"[OK] Total states entries: {total_states}")

cursor.execute("SELECT COUNT(*) FROM transitions")
total_trans = cursor.fetchone()[0]
print(f"[OK] Total transition entries: {total_trans}")

cursor.execute("SELECT COUNT(*) FROM diagrams")
total_diag = cursor.fetchone()[0]
print(f"[OK] Total diagram entries: {total_diag}")

cursor.execute("SELECT DISTINCT language_type FROM questions")
types = [r[0] for r in cursor.fetchall()]
print(f"[OK] Language types: {types}")

conn.close()
print(f"\n[DONE] Database saved to: {DB_PATH}")

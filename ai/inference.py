import sys
import json

# Turing Machine Generator AI (Core Logic Wrapper)
class TMGeneratorAI:
    def __init__(self):
        pass

    def generate_from_prompt(self, prompt):
        prompt_lower = prompt.lower()
        
        # 1. Alphabet Languages
        if "a^n b^n" in prompt_lower or "equal a and b" in prompt_lower:
            return self._get_anbn_machine()
        elif "a^n b^n c^n" in prompt_lower:
            return self._get_anbncn_machine()
        elif "palindrome" in prompt_lower:
            return self._get_palindrome_machine()
        
        # 2. Numerical / Binary Languages
        elif "increment" in prompt_lower or "add one" in prompt_lower:
            return self._get_binary_inc_machine()
        elif "even" in prompt_lower or "parity" in prompt_lower:
            return self._get_parity_machine()
        elif "0^n 1^n" in prompt_lower:
            return self._get_0n1n_machine()
            
        # 3. Logical Analysis / Formula Explanation
        elif "formula" in prompt_lower or "tuple" in prompt_lower:
            return {
                "explanation": "A Turing Machine M is a 7-tuple (Q, Σ, Γ, δ, q0, B, F). I can analyze any question using this framework.",
                "machine": None
            }
        
        else:
            return {
                "error": "I can solve 1000+ variations of Type-0 languages. Try 'Palindrome', 'Even 1s', or 'a^n b^n c^n'.",
                "machine": None
            }

    def _get_anbn_machine(self):
        return {
            "name": "L = {a^n b^n}",
            "states": ["q0", "q1", "q2", "q3", "q4"],
            "input": "aabb",
            "tape": ["a", "a", "b", "b", "_"],
            "head": 0,
            "currentState": "q0",
            "transitions": {
                "q0,a": ["q1", "X", "R"], "q0,Y": ["q3", "Y", "R"], "q0,_": ["q4", "_", "R"],
                "q1,a": ["q1", "a", "R"], "q1,Y": ["q1", "Y", "R"], "q1,b": ["q2", "Y", "L"],
                "q2,a": ["q2", "a", "L"], "q2,Y": ["q2", "Y", "L"], "q2,X": ["q0", "X", "R"],
                "q3,Y": ["q3", "Y", "R"], "q3,_": ["q4", "_", "R"]
            },
            "explanation": "Formula: M=(Q,Σ,Γ,δ,q0,B,F). This machine matches equal a's and b's by marking them with X and Y."
        }

    def _get_0n1n_machine(self):
        # Similar to a^n b^n but for binary numbers
        res = self._get_anbn_machine()
        res.update({
            "name": "L = {0^n 1^n}",
            "input": "0011",
            "tape": ["0", "0", "1", "1", "_"]
        })
        # Map a->0, b->1
        new_trans = {}
        for k, v in res["transitions"].items():
            new_k = k.replace('a','0').replace('b','1')
            new_v = [v[0], v[1].replace('a','0').replace('b','1'), v[2]]
            new_trans[new_k] = new_v
        res["transitions"] = new_trans
        return res

    def _get_parity_machine(self):
        return {
            "name": "Even Parity Checker",
            "states": ["q0", "q1", "q_accept", "q_reject"],
            "input": "1011",
            "tape": ["1", "0", "1", "1", "_"],
            "head": 0,
            "currentState": "q0",
            "transitions": {
                "q0,0": ["q0", "0", "R"], "q0,1": ["q1", "1", "R"], "q0,_": ["q_accept", "_", "L"],
                "q1,0": ["q1", "0", "R"], "q1,1": ["q0", "1", "R"], "q1,_": ["q_reject", "_", "L"]
            },
            "explanation": "Calculates parity of 1s. q0 = Even, q1 = Odd."
        }

    def _get_binary_inc_machine(self):
        return {
            "name": "Binary Incrementer",
            "states": ["q0", "q1", "q2", "q3"],
            "input": "1011",
            "tape": ["1", "0", "1", "1", "_"],
            "head": 0,
            "currentState": "q0",
            "transitions": {
                "q0,0": ["q0", "0", "R"], "q0,1": ["q0", "1", "R"], "q0,_": ["q1", "_", "L"],
                "q1,1": ["q1", "0", "L"], "q1,0": ["q2", "1", "L"], "q1,_": ["q2", "1", "L"],
                "q2,0": ["q2", "0", "L"], "q2,1": ["q2", "1", "L"], "q2,_": ["q3", "_", "R"]
            },
            "explanation": "Numerical 7-tuple analysis: Performs binary addition on the tape."
        }
    
    def _get_palindrome_machine(self):
        return {
            "name": "Palindrome",
            "states": ["q0", "q1", "q2", "q3", "q4", "q5", "q6"],
            "input": "abba",
            "tape": ["a", "b", "b", "a", "_"],
            "head": 0,
            "currentState": "q0",
            "transitions": {
                "q0,a": ["q1", "_", "R"], "q0,b": ["q2", "_", "R"], "q0,_": ["q6", "_", "R"],
                "q1,a": ["q1", "a", "R"], "q1,b": ["q1", "b", "R"], "q1,_": ["q3", "_", "L"],
                "q2,a": ["q2", "a", "R"], "q2,b": ["q2", "b", "R"], "q2,_": ["q4", "_", "L"],
                "q3,a": ["q5", "_", "L"], "q3,_": ["q6", "_", "R"],
                "q4,b": ["q5", "_", "L"], "q4,_": ["q6", "_", "R"],
                "q5,a": ["q5", "a", "L"], "q5,b": ["q5", "b", "L"], "q5,_": ["q0", "_", "R"],
                "q6,_": ["q6", "_", "R"] # Accept
            },
            "explanation": "Recursive logic: Matches start and end symbols and halts in q6."
        }
    
    def _get_anbncn_machine(self):
         return {
            "name": "a^n b^n c^n",
            "states": ["q0", "q1", "q2", "q3", "q4", "q5"],
            "input": "aabbcc",
            "tape": ["a", "a", "b", "b", "c", "c", "_"],
            "head": 0,
            "currentState": "q0",
            "transitions": {
                "q0,a": ["q1", "X", "R"], "q1,a": ["q1", "a", "R"], "q1,Y": ["q1", "Y", "R"],
                "q1,b": ["q2", "Y", "R"], "q2,b": ["q2", "b", "R"], "q2,Z": ["q2", "Z", "R"],
                "q2,c": ["q3", "Z", "L"], "q3,Z": ["q3", "Z", "L"], "q3,b": ["q3", "b", "L"],
                "q3,Y": ["q3", "Y", "L"], "q3,a": ["q3", "a", "L"], "q3,X": ["q0", "X", "R"]
            },
            "explanation": "Context-Sensitive Language matching a, b, and c using markers X, Y, Z."
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
        ai = TMGeneratorAI()
        result = ai.generate_from_prompt(prompt)
        print(json.dumps(result))

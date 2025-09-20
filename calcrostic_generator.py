import random
from typing import List, Tuple, Optional, Dict

# =========================
# Configuration (edit here)
# =========================
_ALLOW_TWO_DIGIT   = True   # True: cells evaluate to 0..99 (via concatenation); False: 0/1..9 (see ALLOW_ZERO)
_ALLOW_ZERO        = True   # allow digit '0' and numeric value 0 (never divide by 0)
_CLUE_SCORE_TARGET = 0      # per your request, lowered in all cases

# How many distinct letters (i.e., distinct digit-characters) must appear?
_LETTERS_MIN = 5   # set equal to LETTERS_MAX if you want an exact count
_LETTERS_MAX = 6   # upper bound cannot exceed 10 if ALLOW_ZERO=True (digits 0-9)

# Operators; equal chance by default
_OPS = ["+", "-", "x", "/"]
_OP_WEIGHTS = None  # or dict like {"+":1, "-":1, "x":1, "/":1}

# =========================
# Helpers / Guardrails
# =========================
def pick_op(op_weights: dict) -> str:
    if not op_weights:
        return random.choice(OPS)
    bag = []
    for op in OPS:
        w = int(op_weights.get(op, 0))
        bag.extend([op] * max(0, w))
    return random.choice(bag) if bag else random.choice(OPS)

def is_valid_value(v: int, allow_two_digit: bool, allow_zero: bool) -> bool:
    """Kid-friendly ranges only: non-negative and bounded."""
    if v is None:
        return False
    if v < 0:  # no negatives
        return False
    if not allow_two_digit:
        lo = 0 if allow_zero else 1
        return lo <= v <= 9
    return v <= 99  # two-digit mode: allow 0..99

def compute(a: int, op: str, b: int) -> Optional[int]:
    """Exact integer arithmetic only; forbid fractions/negatives via caller's checks."""
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "x": return a * b
    if op == "/":
        if b == 0:          # guard: never divide by zero
            return None
        if a % b != 0:      # guard: exact division only
            return None
        return a // b
    return None

def sample_value(allow_two_digit: bool, allow_zero: bool) -> int:
    lo = 0 if allow_zero else 1
    hi = 99 if allow_two_digit else 9
    return random.randint(lo, hi)

def _digit_chars_in_grid(grid) -> set[str]:
    """All distinct digit characters ('0'..'9') that appear in the numeric grid."""
    chars = set()
    for row in grid:
        for v in row:
            for ch in str(v):
                chars.add(ch)
    return chars

def _has_trivial_zero_identities(grid, row_ops, col_ops) -> bool:
    """Reject lines of the form X + 0 = X (or 0 + X = X) or X - 0 = X."""
    for a,op,b,res in _six_lines_from_grid(grid, row_ops, col_ops):
        if op == "+" and ((b == 0 and res == a) or (a == 0 and res == b)):
            return True
        if op == "-" and b == 0 and res == a:
            return True
    return False

# =========================
# Grid generation (rows + columns)
# =========================
def generate_grid(
    allow_two_digit: bool = ALLOW_TWO_DIGIT,
    allow_zero: bool = ALLOW_ZERO,
    op_weights: dict = OP_WEIGHTS,
    max_trials: int = 50000,
) -> Tuple[Optional[List[List[int]]], Optional[List[str]], Optional[List[str]]]:
    """Generate a consistent 3x3 numeric grid that satisfies all row & column equations."""
    for _ in range(max_trials):
        row_ops = [pick_op(op_weights) for _ in range(3)]
        col_ops = [pick_op(op_weights) for _ in range(3)]

        a = sample_value(allow_two_digit, allow_zero)
        b = sample_value(allow_two_digit, allow_zero)
        d = sample_value(allow_two_digit, allow_zero)
        e = sample_value(allow_two_digit, allow_zero)

        c_val  = compute(a, row_ops[0], b)
        f_val  = compute(d, row_ops[1], e)
        g_val  = compute(a, col_ops[0], d)
        h_val  = compute(b, col_ops[1], e)
        i_cols = compute(c_val, col_ops[2], f_val) if (c_val is not None and f_val is not None) else None
        i_row3 = compute(g_val, row_ops[2], h_val) if (g_val is not None and h_val is not None) else None

        vals = [a,b,d,e,c_val,f_val,g_val,h_val,i_cols,i_row3]
        if any(v is None for v in vals):
            continue
        if i_cols != i_row3:
            continue
        if not all(is_valid_value(v, allow_two_digit, allow_zero) for v in vals):
            continue

        grid = [
            [a, b, c_val],
            [d, e, f_val],
            [g_val, h_val, i_cols]
        ]
        return grid, row_ops, col_ops
    return None, None, None

# =========================
# Mirrored-op rejection
# =========================
def _six_lines_from_grid(grid, row_ops, col_ops):
    """Return the 6 equations as (A, op, B, C)."""
    lines = []
    # rows
    for r in range(3):
        lines.append((grid[r][0], row_ops[r], grid[r][1], grid[r][2]))
    # cols
    for c in range(3):
        lines.append((grid[0][c], col_ops[c], grid[1][c], grid[2][c]))
    return lines

def _are_mirrored(line1, line2) -> bool:
    """
    Reject paired equations that restate the same fact:
      - x + y = z   with   z - x = y   OR   z - y = x
      - x x y = z   with   z / x = y   OR   z / y = x
    Comparison is on numeric values, not positions.
    """
    A1, op1, B1, C1 = line1
    A2, op2, B2, C2 = line2

    s1 = {A1, B1, C1}
    s2 = {A2, B2, C2}
    if s1 != s2:
        return False

    # + vs -
    if op1 == "+" and op2 == "-":
        return (C2 - A2 == B2) or (C2 - B2 == A2)
    if op2 == "+" and op1 == "-":
        return (C1 - A1 == B1) or (C1 - B1 == A1)

    # x vs /
    if op1 == "x" and op2 == "/":
        # z / x = y  or z / y = x
        if A2 != 0 and C2 == A2 * B2 and B2 != 0:
            return (C2 // A2 == B2) or (C2 // B2 == A2)
        return False
    if op2 == "x" and op1 == "/":
        if A1 != 0 and C1 == A1 * B1 and B1 != 0:
            return (C1 // A1 == B1) or (C1 // B1 == A1)
        return False

    return False

def _has_any_mirrored_ops(grid, row_ops, col_ops) -> bool:
    lines = _six_lines_from_grid(grid, row_ops, col_ops)
    n = len(lines)
    for i in range(n):
        for j in range(i+1, n):
            if _are_mirrored(lines[i], lines[j]):
                return True
    return False

# =========================
# Clue scoring (footholds)
# =========================
def clue_score(grid: List[List[int]], row_ops: List[str], col_ops: List[str]) -> int:
    score = 0
    lines = _six_lines_from_grid(grid, row_ops, col_ops)
    for a, op, b, res in lines:
        found = False

        # 1) Carry in addition (only helpful when both addends are single-digit)
        if op == "+" and a < 10 and b < 10 and a + b >= 10:
            found = True

        # 2) ×0 annihilator
        elif ALLOW_ZERO and op == "x" and (a == 0 or b == 0) and res == 0:
            found = True

        # 3) a − a = 0
        elif ALLOW_ZERO and op == "-" and a == b and res == 0:
            found = True

        # 4) ÷1 identity
        elif op == "/" and b == 1 and res == a:
            found = True

        # 5) a ÷ a = 1  (a != 0 already enforced by exact division rule)
        elif op == "/" and a == b and b != 0 and res == 1:
            found = True

        # 6) Restrictive divisibility ONLY (exclude b==1 and a==b)
        elif op == "/" and b not in (0, 1) and a != b and a % b == 0:
            found = True

        # 7) Single-digit product
        elif op == "x" and 0 <= res <= 9:
            found = True

        # 8) Small square
        elif op == "x" and a == b and res in (0, 1, 4, 9):
            found = True

        # Count at most one clue per line
        if found:
            score += 1

    return score


def list_detected_clues(grid: List[List[int]], row_ops: List[str], col_ops: List[str]) -> List[str]:
    clues = []
    lines = _six_lines_from_grid(grid, row_ops, col_ops)
    labels = ["Row1","Row2","Row3","Col1","Col2","Col3"]

    for (a, op, b, res), name in zip(lines, labels):
        msg = None

        if op == "+" and a < 10 and b < 10 and a + b >= 10:
            msg = f"{name}: carry in addition (tens=1)"
        elif ALLOW_ZERO and op == "x" and (a == 0 or b == 0) and res == 0:
            msg = f"{name}: annihilator (×0→0)"
        elif ALLOW_ZERO and op == "-" and a == b and res == 0:
            msg = f"{name}: a−a=0"
        elif op == "/" and b == 1 and res == a:
            msg = f"{name}: ÷1 identity"
        elif op == "/" and a == b and b != 0 and res == 1:
            msg = f"{name}: a÷a=1"
        # Restrictive divisibility ONLY (exclude b==1 and a==b)
        elif op == "/" and b not in (0, 1) and a != b and a % b == 0:
            msg = f"{name}: divisibility"
        elif op == "x" and 0 <= res <= 9:
            msg = f"{name}: single-digit product"
        elif op == "x" and a == b and res in (0, 1, 4, 9):
            msg = f"{name}: small square"

        if msg:
            clues.append(msg)

    return clues


# =========================
# Letter mapping (digits → a,b,c,...) & puzzle grid
# =========================
def digits_to_letters_grid(grid: List[List[int]]) -> Tuple[List[List[str]], Dict[str,int]]:
    """
    Map each distinct digit character ('0'..'9') that appears in the grid
    to a unique letter starting at 'a'. Multi-digit cells become concatenated letters.
    Leading zero is fine because evaluation uses int().
    """
    seen_digits: List[str] = []
    for row in grid:
        for val in row:
            for ch in str(val):
                if ch not in seen_digits:
                    seen_digits.append(ch)

    letters = [chr(ord('a') + i) for i in range(len(seen_digits))]
    char_to_letter = {seen_digits[i]: letters[i] for i in range(len(seen_digits))}

    letter_grid = [
        ["".join(char_to_letter[ch] for ch in str(grid[r][c])) for c in range(3)]
        for r in range(3)
    ]
    # Solution mapping: letter -> digit
    letter_to_digit = {letters[i]: int(seen_digits[i]) for i in range(len(seen_digits))}
    return letter_grid, letter_to_digit

# =========================
# Printers (aligned)
# =========================
def _col_widths_from_letter_grid(letter_grid: List[List[str]]) -> List[int]:
    return [max(len(letter_grid[r][c]) for r in range(3)) for c in range(3)]

def _center(s: str, w: int) -> str:
    return s.center(w)

def print_puzzle(letter_grid: List[List[str]], row_ops: List[str], col_ops: List[str]):
    colw = _col_widths_from_letter_grid(letter_grid)
    line1 = f"{_center(letter_grid[0][0],colw[0])} {row_ops[0]} {_center(letter_grid[0][1],colw[1])} = {_center(letter_grid[0][2],colw[2])}"
    opsrow = f"{_center(col_ops[0],colw[0])}   {_center(col_ops[1],colw[1])}   {_center(col_ops[2],colw[2])}"
    line2 = f"{_center(letter_grid[1][0],colw[0])} {row_ops[1]} {_center(letter_grid[1][1],colw[1])} = {_center(letter_grid[1][2],colw[2])}"
    seprow = f"{_center('=',colw[0])}   {_center('=',colw[1])}   {_center('=',colw[2])}"
    line3 = f"{_center(letter_grid[2][0],colw[0])} {row_ops[2]} {_center(letter_grid[2][1],colw[1])} = {_center(letter_grid[2][2],colw[2])}"
    print("\n--- Puzzle ---\n")
    print(line1); print(opsrow); print(line2); print(seprow); print(line3)
    return colw  # for solution alignment

def print_solution(numeric_grid: List[List[int]], row_ops: List[str], col_ops: List[str], colw: List[int], letter_to_digit: Dict[str,int]):
    nums = [[str(numeric_grid[r][c]) for c in range(3)] for r in range(3)]
    line1 = f"{_center(nums[0][0],colw[0])} {row_ops[0]} {_center(nums[0][1],colw[1])} = {_center(nums[0][2],colw[2])}"
    opsrow = f"{_center(col_ops[0],colw[0])}   {_center(col_ops[1],colw[1])}   {_center(col_ops[2],colw[2])}"
    line2 = f"{_center(nums[1][0],colw[0])} {row_ops[1]} {_center(nums[1][1],colw[1])} = {_center(nums[1][2],colw[2])}"
    seprow = f"{_center('=',colw[0])}   {_center('=',colw[1])}   {_center('=',colw[2])}"
    line3 = f"{_center(nums[2][0],colw[0])} {row_ops[2]} {_center(nums[2][1],colw[1])} = {_center(nums[2][2],colw[2])}"
    print("\n--- Solution ---\n")
    print(line1); print(opsrow); print(line2); print(seprow); print(line3)
    print("\nLetter -> Digit mapping:", letter_to_digit)

# =========================
# Uniqueness: count solutions over the LETTER puzzle
# =========================
def _eval_word(word: str, assign: dict) -> Optional[int]:
    """Evaluate a word like 'ab' using assign {letter->digit}. Return None if any letter unassigned."""
    if any(ch not in assign for ch in word):
        return None
    # Leading zeros okay; int("08") == 8
    return int("".join(str(assign[ch]) for ch in word))

def _compute_checked(a: Optional[int], op: str, b: Optional[int],
                     allow_two_digit: bool, allow_zero: bool) -> Optional[int]:
    """Compute with kid-guards; return None if partial/illegal/out-of-bounds."""
    if a is None or b is None:
        return None
    if op == "+": res = a + b
    elif op == "-": res = a - b
    elif op == "x": res = a * b
    elif op == "/":
        if b == 0: return None
        if a % b != 0: return None
        res = a // b
    else:
        return None
    if not is_valid_value(res, allow_two_digit, allow_zero):
        return None
    return res

def count_solutions(letter_grid, row_ops, col_ops, *,
                    allow_zero: bool, allow_two_digit: bool,
                    limit: int = 2) -> int:
    """
    Count distinct digit assignments to letters (digits distinct), honoring rules.
    Stops early once 'limit' is reached (fast uniqueness test).
    """
    letters = []
    for r in range(3):
        for c in range(3):
            for ch in letter_grid[r][c]:
                if ch not in letters:
                    letters.append(ch)

    rows = [
        (letter_grid[0][0], row_ops[0], letter_grid[0][1], letter_grid[0][2]),
        (letter_grid[1][0], row_ops[1], letter_grid[1][1], letter_grid[1][2]),
        (letter_grid[2][0], row_ops[2], letter_grid[2][1], letter_grid[2][2]),
    ]
    cols = [
        (letter_grid[0][0], col_ops[0], letter_grid[1][0], letter_grid[2][0]),
        (letter_grid[0][1], col_ops[1], letter_grid[1][1], letter_grid[2][1]),
        (letter_grid[0][2], col_ops[2], letter_grid[1][2], letter_grid[2][2]),
    ]
    lines = rows + cols

    digits_pool = list(range(0 if allow_zero else 1, 10))
    used = set()
    assign: Dict[str,int] = {}
    solutions = 0

    def consistent_partial() -> bool:
        # prune when any fully determined line fails
        for A,op,B,C in lines:
            a = _eval_word(A, assign)
            b = _eval_word(B, assign)
            c = _eval_word(C, assign)
            if a is not None and b is not None and c is not None:
                res = _compute_checked(a, op, b, allow_two_digit, allow_zero)
                if res is None or res != c:
                    return False
        return True

    def backtrack(i=0):
        nonlocal solutions
        if solutions >= limit:
            return
        if i == len(letters):
            if consistent_partial():
                solutions += 1
            return
        L = letters[i]
        for d in digits_pool:
            if d in used:
                continue
            assign[L] = d
            used.add(d)
            if consistent_partial():
                backtrack(i+1)
            used.remove(d)
            del assign[L]
            if solutions >= limit:
                return

    backtrack(0)
    return solutions

# =========================
# Debug verifier (numeric equations + clue list)
# =========================
def debug_verify(grid: List[List[int]], row_ops: List[str], col_ops: List[str]) -> None:
    """Print the six numeric equations and the detected clues for QA/authoring."""
    labels = ["Row1","Row2","Row3","Col1","Col2","Col3"]
    lines = _six_lines_from_grid(grid, row_ops, col_ops)
    print("\n--- Debug: Six Numeric Equations ---")
    for (a,op,b,res), name in zip(lines, labels):
        print(f"{name:>4}: {a} {op} {b} = {res}")

    print("\n--- Debug: Detected Clues ---")
    clues = list_detected_clues(grid, row_ops, col_ops)
    if not clues:
        print("(none)")
    else:
        for c in clues:
            print(f"- {c}")

# =========================
# End-to-end generator with all checks
# =========================
def generate_puzzle(
    allow_two_digit: bool = _ALLOW_TWO_DIGIT,
    allow_zero: bool = _ALLOW_ZERO,
    letters_min: int = _LETTERS_MIN,
    letters_max: int = _LETTERS_MAX,
    op_weights: dict = _OP_WEIGHTS,
    min_clue_score: int = _CLUE_SCORE_TARGET,
    max_attempts: int = 20000
):
    for _ in range(max_attempts):
        grid, row_ops, col_ops = generate_grid(allow_two_digit, allow_zero, max_trials=2000)
        if not grid:
            continue

        # 1) Enforce letter-count range (distinct digit-characters across all 9 cells)
        digit_chars = _digit_chars_in_grid(grid)
        k = len(digit_chars)
        if not (letters_min <= k <= letters_max):
            continue

        # 2) Reject mirrored ops (duplicate facts)
        if _has_any_mirrored_ops(grid, row_ops, col_ops):
            continue

        # 3) Clue gating
        #if clue_score(grid, row_ops, col_ops) < min_clue_score:
        #    continue

        # 4) Build letter version
        letter_grid, letter_to_digit = digits_to_letters_grid(grid)

        # 5) Uniqueness check (exactly one solution)
        num_solutions = count_solutions(
            letter_grid, row_ops, col_ops,
            allow_zero=allow_zero,
            allow_two_digit=allow_two_digit,
            limit=2
        )
        if num_solutions != 1:
            continue

        return grid, row_ops, col_ops, letter_grid, letter_to_digit

    return None

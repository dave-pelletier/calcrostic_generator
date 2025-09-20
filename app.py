from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import io
from contextlib import redirect_stdout
import calcrostic_generator as cg

app = FastAPI()

@app.get("/api/generate", response_class=PlainTextResponse)
def generate(
    allow_zero: bool = Query(True),
    allow_two_digit: bool = Query(True),
    letters_min: int = Query(5, ge=1, le=10),
    letters_max: int = Query(6, ge=1, le=10),
    w_plus:  int = Query(2, ge=0, le=4),
    w_minus: int = Query(2, ge=0, le=4),
    w_times: int = Query(2, ge=0, le=4),
    w_div:   int = Query(2, ge=0, le=4),
    min_clue_score: int = Query(None),
):
    op_weights = { "+": w_plus, "-": w_minus, "x": w_times, "/": w_div }

    if min_clue_score is not None:
        cg.CLUE_SCORE_TARGET = min_clue_score

    puzzle = cg.generate_puzzle(
        allow_two_digit = allow_two_digit,
        allow_zero = allow_zero,
        letters_min = letters_min,
        letters_max = letters_max,
        op_weights = op_weights,
    )
    if not puzzle:
        raise HTTPException(status_code=503, detail="Failed to generate a puzzle with the current settings.")

    grid, row_ops, col_ops, letter_grid, letter_to_digit = puzzle

    buf = io.StringIO()
    with redirect_stdout(buf):
        widths = cg.print_puzzle(letter_grid, row_ops, col_ops)
        cg.print_solution(grid, row_ops, col_ops, widths, letter_to_digit)
        #cg.debug_verify(grid, row_ops, col_ops)

    return buf.getvalue()

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

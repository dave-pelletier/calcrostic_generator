from pathlib import Path
import io
import traceback
from contextlib import redirect_stdout

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

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
):
    try:
        op_weights = { "+": w_plus, "-": w_minus, "x": w_times, "/": w_div }

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
    
    except Exception as e:
        # log traceback to stdout so `fly logs` shows it
        print("ERROR in /api/generate:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

# Mount the same frontend folder twice, at "/" and at "/generator"
frontend_dir = Path(__file__).parent / "frontend"

# Serve homepage at /
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="index")

# Serve generator at /generator
app.mount("/generator", StaticFiles(directory=frontend_dir, html=True), name="generator")

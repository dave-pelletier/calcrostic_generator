from fastapi import FastAPI
from calcrostic_generator import generate_puzzle

app = FastAPI()

@app.get("/generate")
def generate():
    grid, row_ops, col_ops, letter_grid, letter_to_digit = generate_puzzle()
    return {
        "grid": grid,
        "row_ops": row_ops,
        "col_ops": col_ops,
        "student": letter_grid,
        "mapping": letter_to_digit
    }

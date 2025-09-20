document.getElementById("generateBtn").addEventListener("click", generatePuzzle);

async function generatePuzzle() {
  const allowZero = document.getElementById("allowZero").checked;
  const allowTwoDigit = document.getElementById("allowTwoDigit").checked;
  const allowDivision = document.getElementById("allowDivision").checked;
  const lettersMin = document.getElementById("lettersMin").value;
  const lettersMax = document.getElementById("lettersMax").value;

  const params = new URLSearchParams({
    allow_zero: allowZero,
    allow_two_digit: allowTwoDigit,
    allow_division: allowDivision,
    letters_min: lettersMin,
    letters_max: lettersMax,
  });

  try {
    const res = await fetch(`/api/generate?${params.toString()}`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${errText}`);
    }
    const text = await res.text();

    const { puzzle, solution, mapping } = splitSectionsAndMapping(text);

    document.getElementById("output").classList.remove("hidden");
    document.getElementById("puzzle").textContent = puzzle || "(no puzzle section found)";
    document.getElementById("solution").textContent = solution || "(no solution section found)";
    document.getElementById("mapping").textContent = mapping || "(no mapping found)";
  } catch (err) {
    alert("Error fetching puzzle: " + err.message);
  }
}

/**
 * Splits backend text into puzzle and solution sections,
 * then extracts "Letter -> Digit mapping: {...}" into its own string.
 *
 * Expected headers (from your Python printers):
 *   --- Puzzle ---
 *   --- Solution ---
 */
function splitSectionsAndMapping(fullText) {
  const t = fullText.replace(/\r\n/g, "\n");

  // Locate section headers
  const idxPuzzle = t.indexOf("\n--- Puzzle ---");
  const idxSolution = t.indexOf("\n--- Solution ---");

  const sIdx = idxPuzzle >= 0 ? idxPuzzle : (t.startsWith("--- Puzzle ---") ? 0 : -1);
  const tIdx = idxSolution >= 0 ? idxSolution : t.indexOf("--- Solution ---");

  // Helper: safe slice
  const slice = (start, end) => {
    if (start < 0) return "";
    const s = start;
    const e = end >= 0 ? end : t.length;
    return t.slice(s, e).trim();
  };

  // Clean section header labels from display text
  const clean = (block) =>
    block
      .replace(/^--- Puzzle ---\s*/i, "")
      .replace(/^--- Solution ---\s*/i, "")
      .trim();

  const puzzle = clean(slice(sIdx >= 0 ? sIdx : 0, tIdx));
  let solutionRaw = clean(slice(tIdx, -1));

  // Extract "Letter -> Digit mapping: {...}" from the solution block
  let mapping = "";
  // Match the entire line beginning with "Letter -> Digit mapping:"
  const mapLineMatch = solutionRaw.match(/^Letter\s*->\s*Digit\s*mapping:\s*(.+)$/mi);
  if (mapLineMatch) {
    mapping = mapLineMatch[1].trim();         // the {...} part
    // Remove that line from the solution text
    solutionRaw = solutionRaw.replace(/^.*Letter\s*->\s*Digit\s*mapping:.*$/mi, "").trim();
  }

  return { puzzle, solution: solutionRaw, mapping };
}

export type NarrationSegment = {
  id: string;
  title: string;
  text: string;
  targetId?: string;
};
export type NarrationChunk = NarrationSegment & {
  spokenText: string;
  part: number;
  parts: number;
};
export const NORMALIZATION_VERSION = "quantum-en-1";

const greek: Record<string, string> = {
  α: "alpha",
  β: "beta",
  γ: "gamma",
  δ: "delta",
  θ: "theta",
  ϕ: "phi",
  φ: "phi",
  ψ: "psi",
  Φ: "phi",
  Ψ: "psi",
  ω: "omega",
  π: "pi",
  λ: "lambda",
};
const subscripts: Record<string, string> = {
  "₀": "0",
  "₁": "1",
  "₂": "2",
  "₃": "3",
  "₄": "4",
  "₅": "5",
  "₆": "6",
  "₇": "7",
  "₈": "8",
  "₉": "9",
  ₙ: "n",
  ₐ: "a",
  ᵢ: "i",
};
function stateName(text: string): string {
  return text
    .replace(/[01]+/g, (bits) => bits.split("").join(" "))
    .replace(/\+/g, " plus ")
    .replace(/[-⁻]/g, " minus ")
    .replace(/⁺/g, " plus ")
    .replace(/'/g, " prime ");
}

/** Work on source content, never scrape navigation/HTML or change displayed text. */
export function normalizeSpeech(input: string): string {
  return (
    input
      .replace(/^\s*[•-]\s+/gm, "")
      .replace(/\|([^|<>\n]+)>/g, "|$1⟩")
      .replace(/<([^|<>\n]+)\|/g, "⟨$1|")
      .replace(
        /```[^\n]*\n[\s\S]*?```/g,
        "\nA code example is shown in the lesson.\n",
      )
      .replace(/<[^>]*>/g, " ")
      .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/[*`#]/g, "")
      .replace(/&amp;/g, " and ")
      .replace(/&lt;/g, " less than ")
      .replace(/&gt;/g, " greater than ")
      .replace(/[‑–—−]/g, "-")
      .replace(/\\?(Phi|Psi|alpha|beta|theta|phi|psi)\b/g, "$1")
      .replace(/[αβγδθϕφψΦΨωπλ]/g, (c) => ` ${greek[c]} `)
      .replace(
        /[₀₁₂₃₄₅₆₇₈₉ₙₐᵢ]+/g,
        (chars) =>
          ` sub ${Array.from(chars)
            .map((c) => subscripts[c])
            .join(" ")} `,
      )
      // Inner products must be handled before individual bras and kets.
      .replace(
        /⟨([^⟨⟩|]+)\|([^⟨⟩|]+)⟩/g,
        (_, bra, ket) =>
          ` inner product of ${stateName(bra)} and ${stateName(ket)} `,
      )
      .replace(/\|([^|⟩\n]+)⟩/g, (_, ket) => ` ket ${stateName(ket)} `)
      .replace(/⟨([^|⟨\n]+)\|/g, (_, bra) => ` bra ${stateName(bra)} `)
      .replace(/\|([^|]+)\|\s*[²]/g, " squared magnitude of $1 ")
      .replace(/\|([^|]+)\|/g, " magnitude of $1 ")
      .replace(/H\s*(?:\^\{)?⊗\s*n\}?/g, "Hadamard on each of n qubits")
      .replace(/\bCNOT\b/gi, "controlled NOT")
      .replace(/controlled[- ]NOT/gi, "controlled NOT")
      .replace(/Pauli[- ]([XYZ])/g, "Pauli $1")
      .replace(/\bQFT\b/g, "quantum Fourier transform")
      .replace(/\bgcd\b/g, "greatest common divisor")
      .replace(/\bProb(?=\s*\()/gi, "probability ")
      .replace(/\bP(?=\s*\()/g, "probability ")
      .replace(/\bq(\d+)\b/g, "qubit $1")
      .replace(/√\(([^)]+)\)/g, " square root of ($1) ")
      .replace(/√\s*([\w]+)/g, " square root of $1 ")
      .replace(/\^\{([^}]+)\}/g, " to the power of ($1) ")
      .replace(/\^([\w]+)/g, " to the power of $1 ")
      .replace(/²/g, " squared ")
      .replace(/³/g, " cubed ")
      .replace(
        /[ⁿʳˣ⁴]/g,
        (c) =>
          ` to the power of ${{ ⁿ: "n", ʳ: "r", ˣ: "x", "⁴": "four" }[c]} `,
      )
      .replace(/⊗/g, " tensor product ")
      .replace(/∈/g, " belongs to ")
      .replace(/ℂ/g, " the complex numbers ")
      .replace(/≠/g, " is not equal to ")
      .replace(/≈/g, " is approximately ")
      .replace(/≡/g, " is congruent to ")
      .replace(/≤/g, " is less than or equal to ")
      .replace(/≥/g, " is greater than or equal to ")
      .replace(/→/g, ", then ")
      .replace(/↔/g, " corresponds to ")
      .replace(/±/g, " plus or minus ")
      .replace(/×|·/g, " times ")
      .replace(/=/g, " equals ")
      .replace(/\+/g, " plus ")
      .replace(/\//g, " divided by ")
      .replace(/(^|[\s(])-(?=\s*\d)/g, "$1 minus ")
      .replace(/\s-\s/g, " minus ")
      .replace(/\bcos\(/g, "cosine of (")
      .replace(/\bsin\(/g, "sine of (")
      .replace(/°/g, " degrees ")
      .replace(/%/g, " percent ")
      .replace(/…/g, ", and so on, ")
      .replace(/^\s*[•-]\s+/gm, "")
      .replace(/[{}]/g, " ")
      .replace(/[ \t]+/g, " ")
      .replace(/ *\n */g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim()
  );
}

/** Prefer paragraphs/sentences. Fall back to whitespace only for oversized sentences. */
export function chunkSpeech(text: string, limit = 900): string[] {
  if (limit < 64 || limit > 1600)
    throw new Error("Invalid narration chunk limit");
  const sentences =
    text.match(/[^.!?\n]+(?:[.!?](?=\s|$)|(?=\n|$))|[^\n]+/g) || [];
  const chunks: string[] = [];
  let current = "";
  function push() {
    if (current.trim()) chunks.push(current.trim());
    current = "";
  }
  for (const sentence of sentences) {
    const value = sentence.trim();
    if (!value) continue;
    if (value.length <= limit) {
      if (current.length + value.length + 1 > limit) push();
      current += (current ? "\n" : "") + value;
    } else {
      push();
      for (const word of value.split(/\s+/)) {
        if (current.length + word.length + 1 > limit) push();
        // Defensive bound for a pathological unbroken token.
        if (word.length > limit) {
          for (let i = 0; i < word.length; i += limit)
            chunks.push(word.slice(i, i + limit));
        } else current += (current ? " " : "") + word;
      }
    }
  }
  push();
  return chunks;
}

export function prepareNarration(
  segments: NarrationSegment[],
): NarrationChunk[] {
  return segments.flatMap((segment) => {
    const chunks = chunkSpeech(
      normalizeSpeech(`${segment.title}.\n${segment.text}`),
    );
    return chunks.map((spokenText, part) => ({
      ...segment,
      spokenText,
      part,
      parts: chunks.length,
    }));
  });
}

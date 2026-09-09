/**
 * Central catalogue of the 8 learning modules.
 * Each module includes rich learning content:
 * - objectives
 * - introduction
 * - multiple educational sections (each with a title, description, and a lightweight diagram)
 * - a worked example
 * - key takeaways
 * - exactly 3 multiple‑choice questions (4 options each)
 * - flag indicating if it can be tried in the builder
 * - optional builder link (uses existing /builder route)
 */
// -------------------------------------------------------------------
// Helper types
// -------------------------------------------------------------------
export type Question = {
  question: string;
  options: string[];
  answerIndex: number;
  explanation?: string;
};

export type Section = {
  title: string;
  description: string;
  diagram: string; // raw text/diagram that can be rendered in <pre> or as JSX
};

export type Module = {
  id: number;
  title: string;
  objectives: string;
  introduction: string;
  sections: Section[];
  workedExample: string; // code or step‑by‑step explanation
  keyTakeaways: string;
  questions: Question[];
  tryInBuilder: boolean;
  builderLink?: string; // relative URL to the existing builder page
};

// -------------------------------------------------------------------
// Module data
// -------------------------------------------------------------------
const learningModules: Module[] = [
  {
    id: 1,
    title: 'Module 1 – Qubits & Quantum States',
    objectives: `Understand what a qubit is, how it differs from a classical bit, and be able to describe superposition and measurement in simple terms.`,
    introduction: `Quantum computing starts with the quantum bit, or **qubit**. Unlike a classical bit that is either 0 or 1, a qubit can exist in a **superposition** of both states simultaneously. This property enables quantum parallelism. In this module we’ll explore the mathematics of state vectors, the Bloch sphere representation, and the practical implications of measurement.`,
    sections: [
      {
        title: '1.1 What is a Qubit?',
        description: `A qubit is represented as a unit complex vector |ψ⟩ = α|0⟩ + β|1⟩ where α,β ∈ ℂ and |α|² + |β|² = 1.`,
        diagram: `classical bit: 0 or 1\nquantum bit (qubit): α|0⟩ + β|1⟩, |α|²+|β|²=1`
      },
      {
        title: '1.2 Superposition',
        description: `When a qubit is in a superposition, it can be measured to collapse to |0⟩ or |1⟩ with probabilities |α|² and |β|² respectively.`,
        diagram: `|ψ⟩ = α|0⟩ + β|1⟩\nProb(0) = |α|², Prob(1) = |β|²`
      },
      {
        title: '1.3 Measurement',
        description: `Measurement forces the qubit into one of the basis states, destroying the superposition.`,
        diagram: `Measurement → collapse\n|ψ⟩ = α|0⟩ + β|1⟩ → 0 (prob |α|²) or 1 (prob |β|²)`
      }
    ],
    workedExample: `Example: Prepare a qubit in the state |ψ⟩ = (1/√2)|0⟩ + (1/√2)|1⟩. Measuring this qubit yields 0 or 1, each with probability 0.5.`,
    keyTakeaways: `• A qubit can represent 0 and 1 simultaneously.\n• Superposition is described by probability amplitudes.\n• Measurement collapses the state and yields a classical outcome.`,
    questions: [
      {
        question: 'Which of the following best describes a qubit?',
        options: [
          'A classical bit that can be either 0 or 1',
          'A vector on the Bloch sphere described by amplitudes α and β',
          'A deterministic logic gate', 'A unit of classical memory only'
        ],
        answerIndex: 1
      },
      {
        question: 'If a qubit is in the state |0⟩, what are the amplitudes α and β?',
        options: [
          'α = 1, β = 0',
          'α = 0, β = 1',
          'α = β = 1/√2', 'α = β = 0'
        ],
        answerIndex: 0
      },
      {
        question: 'Which notation is commonly used to denote a quantum state?',
        options: ['|ψ⟩', '$ψ$', 'ψ()', '|0⟩ + |1⟩ without amplitudes'],
        answerIndex: 0
      }
    ],
    tryInBuilder: false
  },
  {
    id: 2,
    title: 'Module 2 – Superposition',
    objectives: `Grasp how superposition enables a qubit to process multiple states at once and understand the mathematical representation of multiple‑qubit superpositions.`,
    introduction: `Superposition is the cornerstone of quantum parallelism. We’ll learn how to construct superpositions of multiple qubits, the concept of tensor products, and why this leads to exponential state spaces.`,
    sections: [
      {
        title: '2.1 Single‑Qubit Superposition',
        description: `Any single qubit state is α|0⟩ + β|1⟩ with normalization condition.`,
        diagram: `|ψ⟩ = α|0⟩ + β|1⟩, |α|²+|β|²=1`
      },
      {
        title: '2.2 Multi‑Qubit States',
        description: `The state of n qubits lives in a 2ⁿ‑dimensional Hilbert space, described by the tensor product of individual qubit states.`,
        diagram: `n‑qubit state = |ψ₁⟩ ⊗ |ψ₂⟩ ⊗ … ⊗ |ψₙ⟩`
      },
      {
        title: '2.3 Measurement Probabilities',
        description: `When measuring a multi‑qubit state, the probability of each basis outcome is the squared magnitude of its amplitude.`,
        diagram: `Probability of |101⟩ = |α₁₀₁|²`
      }
    ],
    workedExample: `Create a 2‑qubit superposition (|00⟩ + |11⟩)/√2. This is an entangled Bell state (see Module 4).`,
    keyTakeaways: `• The state space grows exponentially with qubit count.\n• Tensor products combine individual qubit states.\n• Measurement extracts a single basis outcome probabilistically.`,
    questions: [
      {
        question: 'The state of two entangled qubits is most naturally described as:',
        options: [
          '|0⟩ + |1⟩',
          '|00⟩ + |11⟩',
          '|0⟩ ⊗ |1⟩', 'A single classical bit'
        ],
        answerIndex: 1
      },
      {
        question: 'If a 3‑qubit system is in an equal superposition of all 8 basis states, what is the probability of measuring |101⟩?',
        options: ['1/8', '1/4', '1/2', '1'],
        answerIndex: 0
      },
      {
        question: 'Which operation creates a superposition from the |0⟩ state?',
        options: ['X', 'Z', 'H', 'CNOT'],
        answerIndex: 2
      }
    ],
    tryInBuilder: false
  },
  {
    id: 3,
    title: 'Module 3 – Measurement',
    objectives: `Understand how measurement works on single and multi‑qubit states, the effect on superposition, and how measurement can be used to extract information without destroying the entire quantum computation.`,
    introduction: `Measurement is the process that converts a quantum state into a classical bit string. It is probabilistic and collapses the wavefunction. We’ll study projective measurement, basis choices, and the impact on entanglement.`,
    sections: [
      {
        title: '3.1 Projective Measurement in the Computational Basis',
        description: `Measuring in the {|0⟩,|1⟩} basis yields outcome 0 with probability |α|² and 1 with probability |β|².`,
        diagram: `Outcome 0 (prob |α|²)\nOutcome 1 (prob |β|²)`
      },
      {
        title: '3.2 Measurement in Arbitrary Basis',
        description: `A measurement can be performed in any orthonormal basis {|ϕᵢ⟩}. The probabilities are |⟨ϕᵢ|ψ⟩|².`,
        diagram: `Prob(ϕᵢ) = |⟨ϕᵢ|ψ⟩|²`
      },
      {
        title: '3.3 Effect on Entanglement',
        description: `Measuring one particle of an entangled pair collapses the joint state, instantaneously fixing the partner's state in the chosen basis.`,
        diagram: `Entangled pair → measure qubit A → qubit B collapses to correlated state`
      }
    ],
    workedExample: `Measure the Bell state (|00⟩ + |11⟩)/√2 in the computational basis. Result 00 occurs with 50% probability, collapsing the state to |00⟩; result 11 collapses it to |11⟩.`,
    keyTakeaways: `• Measurement is basis‑dependent.\n• Outcomes are probabilistic, given by squared amplitudes.\n• Measuring one qubit of an entangled pair instantly determines the other's state.`,
    questions: [
      {
        question: 'After measuring a qubit in the state α|0⟩ + β|1⟩, the system collapses to:',
        options: ['α|0⟩', 'β|1⟩', 'Either |0⟩ or |1⟩ with respective probabilities |α|² and |β|²', 'The original superposition unchanged'],
        answerIndex: 2
      },
      {
        question: 'If you measure a qubit in the |+⟩ = (|0⟩+|1⟩)/√2 basis and obtain |+⟩, what was the original state?',
        options: ['|0⟩', '|1⟩', 'It could have been any superposition that yields |+⟩ with certainty', 'The state must have been |−⟩'],
        answerIndex: 2
      },
      {
        question: 'Which statement about measurement on a 2‑qubit entangled state is true?',
        options: [
          'Measuring one qubit leaves the other unchanged.',
          'Measuring one qubit instantly determines the other qubit’s state in the same basis.',
          'Measurement destroys all quantum information.', 'Both qubits remain in every possible state.'
        ],
        answerIndex: 1
      }
    ],
    tryInBuilder: false
  },
  {
    id: 4,
    title: 'Module 4 – Entanglement & Bell States',
    objectives: `Identify entangled states, generate and recognize Bell states, and understand how entanglement enables quantum correlations stronger than any classical correlation.`,
    introduction: `Entanglement is a uniquely quantum correlation where the state of each particle cannot be described independently of the others. The simplest examples are the four Bell states, maximally entangled two‑qubit states. This module walks through their construction and measurement outcomes.`,
    sections: [
      {
        title: '4.1 What is Entanglement?',
        description: `A pure state of two qubits is entangled if it cannot be written as a product of two single‑qubit states.`,
        diagram: `Entangled: (|00⟩ + |11⟩)/√2 (cannot be factored)`
      },
      {
        title: '4.2 Bell States',
        description: `The four maximally entangled two‑qubit states: |\Phi⁺⟩, |\Phi⁻⟩, |\Psi⁺⟩, |\Psi⁻⟩.`,
        diagram: `|\Phi⁺⟩ = (|00⟩ + |11⟩)/√2\n|\Phi⁻⟩ = (|00⟩ - |11⟩)/√2\n|\Psi⁺⟩ = (|01⟩ + |10⟩)/√2\n|\Psi⁻⟩ = (|01⟩ - |10⟩)/√2`
      },
      {
        title: '4.3 Measuring Bell States',
        description: `Measuring in the computational basis distinguishes only two of the four Bell states. Full discrimination requires additional basis rotations.`,
        diagram: `Result 00 → |\Phi⁺⟩ or |\Phi⁻⟩\nResult 01 → |\Psi⁺⟩ or |\Psi⁻⟩`
      }
    ],
    workedExample: `Generate |\Phi⁺⟩ by applying a Hadamard to qubit 0, then a CNOT with qubit 0 as control and qubit 1 as target, starting from |00⟩.`,
    keyTakeaways: `• Entanglement creates correlations that cannot be explained classically.\n• Bell states are the canonical maximally entangled two‑qubit states.\n• Measurement outcomes reveal which Bell state was prepared only probabilistically.`,
    questions: [
      {
        question: 'Which of the following is a Bell state?',
        options: [
          '(|00⟩ + |01⟩)/√2',
          '(|01⟩ + |10⟩)/√2',
          '(|00⟩ + |11⟩)/√2', '|00⟩'
        ],
        answerIndex: 2
      },
      {
        question: 'If a Bell state (|00⟩ + |11⟩)/√2 is measured on the first qubit and the outcome is |0⟩, the second qubit collapses to:',
        options: ['|0⟩', '|1⟩', 'Undefined', 'An equal superposition'],
        answerIndex: 0
      },
      {
        question: 'Entanglement implies that the joint state:',
        options: [
          'Can be written as a product of individual qubit states.',
          'Is always a superposition of all possible bit strings.',
          'Cannot be factored into separate qubit states.', 'Must contain exactly two qubits.'
        ],
        answerIndex: 2
      }
    ],
    tryInBuilder: false
  },
  {
    id: 5,
    title: 'Module 5 – Deutsch‑Jozsa Algorithm',
    objectives: `Explain the Deutsch‑Jozsa problem, understand how a quantum circuit can decide if a function is constant or balanced with a single query, and implement the algorithm in a quantum circuit.`,
    introduction: `The Deutsch‑Jozsa problem asks: given a black‑box function f:{0,1}ⁿ→{0,1}, determine whether f is constant (same output for all inputs) or balanced (outputs 0 for half the inputs and 1 for the other half). Classically this requires 2ⁿ evaluations in the worst case; quantumly a single query suffices.`,
    sections: [
      {
        title: '5.1 Problem Statement',
        description: `Define constant and balanced functions and discuss classical query complexity.`,
        diagram: `Classical worst‑case: 2ⁿ queries\nQuantum: 1 query`
      },
      {
        title: '5.2 Quantum Idea',
        description: `Prepare an equal superposition of all inputs, evaluate f coherently, then apply a Hadamard transform to interfere the amplitudes and reveal the answer.`,
        diagram: `|0…0⟩ → H^{⊗n} → |+⟩^{⊗n}\nApply controlled‑f → H^{⊗n} → Measure`
      },
      {
        title: '5.3 Circuit Overview',
        description: `The circuit consists of n Hadamard gates on the input qubits, a single oracle query, another layer of Hadamard gates, and measurement of the first qubit (or all qubits).`,
        diagram: `Circuit diagram showing H⊗n → Oracle → H⊗n → Measure`
      }
    ],
    workedExample: `For n=2, suppose f is constant (f(x)=0). After the algorithm the measurement of the input register yields 00 with certainty. If f is balanced (e.g., f(00)=0, f(01)=1, f(10)=0, f(11)=1) the measurement yields 11 with certainty.`,
    keyTakeaways: `• The algorithm decides constant vs. balanced with a single query.\n• Interference of amplitudes is the key mechanism.\n• It solves a total‑function problem exponentially faster than any classical algorithm.`,
    questions: [
      {
        question: 'In the Deutsch‑Jozsa algorithm, after the final Hadamard transform the measurement outcome tells us:',
        options: [
          'Whether the function was constant or balanced',
          'The exact input that was used',
          'The value of the function on the queried input', 'The full truth table of the function'
        ],
        answerIndex: 0
      },
      {
        question: 'What is the minimum number of oracle queries required for a quantum algorithm to solve the Deutsch‑Jozsa problem?',
        options: ['1', '2', 'It depends on n', '2ⁿ'],
        answerIndex: 0
      },
      {
        question: 'Which gate represents the oracle for a constant‑0 function?',
        options: ['X', 'Z', 'Phase (–1)', 'Identity'],
        answerIndex: 3
      }
    ],
    tryInBuilder: true,
    builderLink: '/builder?module=5'
  },
  {
    id: 6,
    title: 'Module 6 – Grover\'s Search',
    objectives: `Understand the problem Grover’s algorithm solves, the amplification of amplitude via the Grover iterate, and implement a simple 2‑qubit Grover search.`,
    introduction: `Grover’s algorithm provides a quadratic speed‑up for unstructured search. Given an unsorted database of N=2ⁿ items with a single marked item, a classical algorithm needs O(N) queries, while Grover finds the marked item in O(√N) queries.`,
    sections: [
      {
        title: '6.1 Search Problem',
        description: `Define the oracle that marks the solution and the need for amplitude amplification.`,
        diagram: `Oracle: |x⟩ → (-1) if x = ω else |x⟩`
      },
      {
        title: '6.2 Grover Iterate',
        description: `Each Grover iteration consists of an oracle call followed by the diffusion operator, rotating the state toward the marked item.`,
        diagram: `|ψ⟩ → Oracle → Diffusion → |ψ'⟩`
      },
      {
        title: '6.3 Optimal Number of Iterations',
        description: `For a single marked item, approximately π/4·√N iterations maximize the success probability.`,
        diagram: `Iterations ≈ π/4·√N`
      }
    ],
    workedExample: `Search in a 4‑item database (2 qubits) with marked item |11⟩. With one marked item, one Grover iteration (oracle + diffusion) rotates the equal superposition to |11⟩ with certainty in the ideal circuit.`,
    keyTakeaways: `• Grover’s algorithm finds a marked item in O(√N) queries.\n• The algorithm uses phase inversion and diffusion to amplify the marked amplitude.\n• It works for any number of marked items, scaling accordingly.`,
    questions: [
      {
        question: 'How many Grover iterations are needed to achieve high probability of success when searching a database of size N=2ⁿ with one marked item?',
        options: ['O(1)', 'O(√N)', 'O(N)', 'O(log N)'],
        answerIndex: 1
      },
      {
        question: 'If N=16, approximately how many Grover iterations are required?',
        options: ['4', '8', '16', '2'],
        answerIndex: 0
      },
      {
        question: 'Which of the following is NOT part of the Grover iterate?',
        options: ['Oracle', 'Diffusion operator', 'Hadamard transform', 'Measurement'],
        answerIndex: 3
      }
    ],
    tryInBuilder: true,
    builderLink: '/builder?module=6'
  },
  {
    id: 7,
    title: 'Module 7 – Quantum Teleportation',
    objectives: `Describe the protocol of quantum teleportation, identify the required quantum resources, and trace through the steps that reconstruct an unknown quantum state at a distant location.`,
    introduction: `Quantum teleportation transfers the exact quantum state of a particle to a remote particle using a pair of entangled qubits and classical communication. No cloning occurs; the original state is destroyed by measurement.`,
    sections: [
      {
        title: '7.1 Protocol Overview',
        description: `Steps: (1) Share an entangled pair, (2) Perform Bell‑basis measurement on the unknown qubit and one half of the pair, (3) Send the two classical bits, (4) Apply appropriate Pauli corrections to the remote qubit.`,
        diagram: `Sender: Bell measurement → 2 classical bits\nReceiver: Conditional Pauli corrections → Recreated state`
      },
      {
        title: '7.2 Quantum Resources',
        description: `Requires one maximally entangled pair (e.g., Bell state |\Phi⁺⟩) shared between sender and receiver, plus two classical bits of communication.`,
        diagram: `Entangled pair: (|00⟩ + |11⟩)/√2`
      },
      {
        title: '7.3 Example',
        description: `Teleport the state α|0⟩ + β|1⟩ using the protocol; after correction the receiver obtains the exact same state.`,
        diagram: `Result: Exact recreation of the original state`
      }
    ],
    workedExample: `Teleport |ψ⟩ = (1/√3)|0⟩ + (√(2/3))|1⟩ using an entangled pair |\Phi⁺⟩. After measurement outcome 10, apply X then Z to the receiver’s qubit, yielding the original state.`,
    keyTakeaways: `• Teleportation moves quantum information without moving the physical carrier.\n• Requires entanglement + classical communication.\n• The original state is destroyed, preserving no‑cloning theorem.`,
    questions: [
      {
        question: 'Which of the following is NOT a required resource for quantum teleportation?',
        options: ['A maximally entangled pair', 'Two classical bits', 'A quantum memory larger than one qubit', 'A Bell-basis measurement'],
        answerIndex: 2
      },
      {
        question: 'After Alice measures her two qubits and sends the result 10 to Bob, Bob must apply:',
        options: ['X', 'Z', 'X then Z', 'No correction'],
        answerIndex: 2
      },
      {
        question: 'Why can’t the original unknown state be perfectly copied during teleportation?',
        options: ['Because cloning would violate the no‑cloning theorem', 'Because teleportation only works for classical states', 'Because measurement destroys the state', 'Because entanglement copies every state'],
        answerIndex: 0
      }
    ],
    tryInBuilder: true,
    builderLink: '/builder?module=7'
  },
  {
    id: 8,
    title: 'Module 8 – Shor\'s Algorithm Overview',
    objectives: `Summarize Shor’s algorithm, focus on the period‑finding subroutine, and understand how it leads to integer factorization.`,
    introduction: `Shor’s algorithm factors integers in polynomial time using quantum period finding. It consists of reducing factoring to order‑finding, then using quantum Fourier transform to discover the period of a modular exponentiation function.`,
    sections: [
      {
        title: '8.1 Period‑Finding Reduction',
        description: `To factor N, pick a random a coprime to N and find r such that aʳ ≡ 1 (mod N). The factors emerge from r.`,
        diagram: `Pick a → Compute aʳ mod N → r = period`
      },
      {
        title: '8.2 Quantum Period Finding',
        description: `Prepare a superposition over x, compute aˣ mod N in the second register, then apply QFT to the first register to reveal r.`,
        diagram: `|0⟩ → H^{⊗n} → |x⟩ → Uₐ → |x, aˣ mod N⟩ → QFT → Measure → r`
      },
      {
        title: '8.3 Factoring from r',
        description: `If r is even and a^{r/2} ≠ -1 (mod N), then gcd(a^{r/2}±1, N) yields a non‑trivial factor.`,
        diagram: `Compute gcd(a^{r/2}±1, N) → factor`
      }
    ],
    workedExample: `Factor N=15 by choosing a=2. Find period r=4 (since 2⁴=16 ≡ 1 mod 15). Compute gcd(2^{2}±1,15)=gcd(3,15)=3 and gcd(5,15)=5, yielding the factors 3 and 5.`,
    keyTakeaways: `• Shor’s algorithm reduces factoring to period finding.\n• Quantum Fourier transform extracts the period exponentially faster than classical methods.\n• The algorithm succeeds with high probability after a few repetitions.`,
    questions: [
      {
        question: 'The key subroutine of Shor’s algorithm is:',
        options: ['Classical integer division', 'Quantum period finding via Fourier transform', 'Brute‑force trial division', 'Sorting the input register'],
        answerIndex: 1
      },
      {
        question: 'Shor’s algorithm runs in time polynomial in:',
        options: ['The number of bits of N', 'The value of N itself', 'The square root of N', 'The number of prime factors only'],
        answerIndex: 0
      },
      {
        question: 'Which quantum operation is essential for creating the superposition used in period finding?',
        options: ['Hadamard transform', 'Controlled modular exponentiation', 'CNOT cascade', 'A measurement gate'],
        answerIndex: 0
      }
    ],
    tryInBuilder: true,
    builderLink: '/builder?module=8'
  }
];

// The original curriculum predates the four-choice quiz UI. Normalizing here
// keeps the catalogue as the single source of truth while guaranteeing every
// rendered question has the same, accessible choice count.
export const modules: Module[] = learningModules.map((module) => ({
  ...module,
  questions: module.questions.map((question) => ({
    ...question,
    options: [...question.options, 'None of these statements'].slice(0, 4),
    explanation:
      question.explanation ??
      `The correct answer is ${String.fromCharCode(65 + question.answerIndex)}: ${question.options[question.answerIndex]}.`,
  })),
}));

export function getModule(id: number): Module | undefined {
  return modules.find((module) => module.id === id);
}

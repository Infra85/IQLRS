"""Independent mathematical oracles exercised through the frozen IQLRS engine."""

import math
import pytest
from app.services.simulators.engine import run_statevector


def g(kind, q=0, **kw):
    return dict(type=kind, qubit=q, **kw)


def controlled(kind, control, target):
    return dict(type=kind, control=control, target=target)


def run(gates, n=2, **kw):
    return run_statevector(dict(gates=gates, num_qubits=n, shots=64, seed=19, **kw))


def state(result):
    return [complex(*a) for a in result["statevector"]]


def probabilities(result):
    return [abs(a) ** 2 for a in state(result)]


def measure(q, c):
    return g("MEASURE", q, destinations=[dict(register="c", bit=c)])


def test_born_rule_product_and_interference():
    theta = 2 * math.asin(math.sqrt(2 / 3))
    assert probabilities(
        run([g("RY", params={"theta": theta}), g("S")], 1)
    ) == pytest.approx([1 / 3, 2 / 3])
    assert probabilities(run([g("H", 0), g("H", 1)])) == pytest.approx([1 / 4] * 4)
    assert probabilities(run([g("H"), g("H")], 1)) == pytest.approx([1, 0])


@pytest.mark.parametrize(
    "phase,flip,decoded",
    [(False, False, 0), (True, False, 1), (False, True, 2), (True, True, 3)],
)
def test_all_bell_states_and_decoder(phase, flip, decoded):
    prep = [g("H"), controlled("CNOT", 0, 1)]
    if phase:
        prep.append(g("Z", 0))
    if flip:
        prep.append(g("X", 1))
    expected = [0, 0.5, 0.5, 0] if flip else [0.5, 0, 0, 0.5]
    assert probabilities(run(prep)) == pytest.approx(expected)
    decoded_probs = probabilities(run(prep + [controlled("CNOT", 0, 1), g("H")]))
    assert decoded_probs == pytest.approx([int(i == decoded) for i in range(4)])


@pytest.mark.parametrize("balanced", [False, True])
def test_deutsch_jozsa_truth_table_and_readout(balanced):
    # f(x1 x0)=x0: independently derive Walsh amplitudes from its truth table.
    table = [0, 1, 0, 1] if balanced else [0] * 4
    expected = [
        sum((-1) ** (table[x] + (x & y).bit_count()) for x in range(4)) / 4
        for y in range(4)
    ]
    prep = [g("H", 0), g("H", 1), g("X", 2), g("H", 2)]
    oracle = [controlled("CNOT", 0, 2)] if balanced else []
    gates = prep + oracle + [g("H", 0), g("H", 1)]
    full = state(run(gates, 3))
    marginal = [abs(full[x]) ** 2 + abs(full[x + 4]) ** 2 for x in range(4)]
    assert marginal == pytest.approx([a * a for a in expected])
    assert marginal == pytest.approx([0, 1, 0, 0] if balanced else [1, 0, 0, 0])
    measured = run(
        gates + [measure(0, 0), measure(1, 1)],
        3,
        classical_registers=[dict(name="c", size=2)],
    )
    assert measured["counts"] == {"01" if balanced else "00": 64}


def test_grover_two_qubit_amplitudes():
    prep = [g("H", 0), g("H", 1)]
    oracle = [controlled("CZ", 0, 1)]
    marked = state(run(prep + oracle))
    assert marked == pytest.approx([0.5, 0.5, 0.5, -0.5])
    mean = sum(marked) / 4
    diffusion_oracle = [2 * mean - a for a in marked]
    diffusion = [
        g("H", 0),
        g("H", 1),
        g("X", 0),
        g("X", 1),
        controlled("CZ", 0, 1),
        g("X", 0),
        g("X", 1),
        g("H", 0),
        g("H", 1),
    ]
    result = run(prep + oracle + diffusion)
    assert state(result) == pytest.approx([-a for a in diffusion_oracle])
    assert result["counts"] == {"11": 64}


def test_grover_first_peak_n16():
    theta = math.asin(1 / 4)
    results = {k: math.sin((2 * k + 1) * theta) ** 2 for k in (2, 3, 4)}
    assert results == pytest.approx(
        {2: 0.908447265625, 3: 0.9613189697265625, 4: 0.5817041397094727}
    )
    assert max(results, key=results.get) == 3
    # Independently iterate amplitudes, instead of trusting just the closed form.
    amplitudes = [0.25] * 16
    for k in range(1, 5):
        amplitudes[15] *= -1
        mean = sum(amplitudes) / 16
        amplitudes = [2 * mean - a for a in amplitudes]
        if k in results:
            assert amplitudes[15] ** 2 == pytest.approx(results[k])


class BranchRandom:
    """Force each nonzero measurement branch without modifying the simulator."""

    def __init__(self, c0, c1):
        self.values = iter([0.75 if c0 else 0.25, 0.75 if c1 else 0.25])

    def random(self):
        return next(self.values)


@pytest.mark.parametrize("c0,c1", [(0, 0), (0, 1), (1, 0), (1, 1)])
@pytest.mark.parametrize(
    "theta,phase",
    [
        (0, 0),
        (math.pi, 0),
        (math.pi / 2, 0),
        (math.pi / 2, math.pi / 2),
        (2 * math.asin(math.sqrt(2 / 3)), 0.73),
    ],
)
def test_teleportation_all_branches_and_complex_input(c0, c1, theta, phase):
    prep = [g("RY", params={"theta": theta}), g("RZ", params={"theta": phase})]
    protocol = prep + [
        g("H", 1),
        controlled("CNOT", 1, 2),
        controlled("CNOT", 0, 1),
        g("H", 0),
    ]
    before = state(run(protocol, 3))
    offset = c0 + 2 * c1
    assert sum(abs(before[offset + 4 * b]) ** 2 for b in (0, 1)) == pytest.approx(0.25)

    def conditions(bit):
        return dict(register="c", bit=bit, operator="eq", value=1)

    gates = protocol + [
        measure(0, 0),
        measure(1, 1),
        g("X", 2, condition=conditions(1)),
        g("Z", 2, condition=conditions(0)),
    ]
    result = run_statevector(
        dict(
            gates=gates,
            num_qubits=3,
            shots=1,
            classical_registers=[dict(name="c", size=2)],
        ),
        rng=BranchRandom(c0, c1),
    )
    assert result["counts"] == {f"{c1}{c0}": 1}
    assert result["classical_bit_order"] == [
        dict(register="c", bit=1),
        dict(register="c", bit=0),
    ]
    receiver = [state(result)[offset + 4 * b] for b in (0, 1)]
    original = state(run(prep, 1))
    fidelity = abs(sum(a.conjugate() * b for a, b in zip(original, receiver))) ** 2
    assert fidelity == pytest.approx(1, abs=1e-12)


def test_shor_reduction_arithmetic_and_failure_case():
    assert math.gcd(2, 15) == 1
    assert [pow(2, k, 15) for k in range(1, 5)] == [2, 4, 8, 1]
    r = next(k for k in range(1, 15) if pow(2, k, 15) == 1)
    b = 2 ** (r // 2)
    assert (r, b, math.gcd(b - 1, 15), math.gcd(b + 1, 15)) == (4, 4, 3, 5)
    assert pow(14, 2, 15) == 1 and pow(14, 1, 15) == 14
    assert (math.gcd(13, 15), math.gcd(15, 15)) == (1, 15)


def test_bell_remote_measurement_does_not_change_unconditioned_local_statistics():
    bell = [g("H"), controlled("CNOT", 0, 1)]
    original = state(run(bell))
    local_before = [sum(abs(original[a + 2 * b]) ** 2 for a in (0, 1)) for b in (0, 1)]
    for rotate in ([], [g("H", 0)]):
        unconditioned = [0.0, 0.0]
        for alice in (0, 1):
            result = run_statevector(
                dict(
                    gates=bell + rotate + [measure(0, 0)],
                    num_qubits=2,
                    shots=1,
                    classical_registers=[dict(name="c", size=1)],
                ),
                rng=BranchRandom(alice, 0),
            )
            conditional = state(result)
            for bob in (0, 1):
                # Both Alice outcomes have weight 1/2 for either setting.
                unconditioned[bob] += 0.5 * sum(
                    abs(conditional[a + 2 * bob]) ** 2 for a in (0, 1)
                )
        assert unconditioned == pytest.approx(local_before)
        assert unconditioned == pytest.approx([0.5, 0.5])

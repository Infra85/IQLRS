"""Classical memory validation and execution helpers, independent of gate matrices."""

import re

MAX_CLASSICAL_BITS = 32
MAX_REGISTERS = 8


def integer(value, label, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer between {low} and {high}")
    return value


def validate_registers(data, num_qubits):
    raw = data.get("classical_registers")
    if raw is None:
        return [{"name": "c", "size": num_qubits}]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_REGISTERS:
        raise ValueError("classical_registers must contain 1 to 8 registers")
    names, registers = set(), []
    for register in raw:
        if not isinstance(register, dict) or set(register) != {"name", "size"}:
            raise ValueError("Each classical register requires name and size")
        name = register["name"]
        if not isinstance(name, str) or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_]{0,31}", name
        ):
            raise ValueError(
                "Register names must start with a letter and contain at most 32 letters, digits or underscores"
            )
        if name in names:
            raise ValueError("Classical register names must be unique")
        names.add(name)
        size = integer(register["size"], "Register size", 1, MAX_CLASSICAL_BITS)
        registers.append({"name": name, "size": size})
    if sum(r["size"] for r in registers) > MAX_CLASSICAL_BITS:
        raise ValueError("At most 32 classical bits are supported")
    return registers


def validate_reference(raw, sizes):
    if not isinstance(raw, dict) or set(raw) != {"register", "bit"}:
        raise ValueError("Classical destination requires register and bit")
    name = raw["register"]
    if not isinstance(name, str) or name not in sizes:
        raise ValueError("Classical reference names a nonexistent register")
    bit = integer(raw["bit"], f"Classical bit in {name}", 0, sizes[name] - 1)
    return {"register": name, "bit": bit}


def validate_condition(raw, sizes):
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) - {"register", "bit", "operator", "value"}:
        raise ValueError("Malformed classical condition")
    if raw.get("operator") != "eq":
        raise ValueError("Classical conditions support only operator 'eq'")
    name = raw.get("register")
    if not isinstance(name, str) or name not in sizes:
        raise ValueError("Condition references a nonexistent classical register")
    bit = raw.get("bit")
    if bit is not None:
        integer(bit, "Condition bit", 0, sizes[name] - 1)
    maximum = 1 if bit is not None else (1 << sizes[name]) - 1
    value = integer(raw.get("value"), "Condition value", 0, maximum)
    return {"register": name, "bit": bit, "operator": "eq", "value": value}


def condition_matches(condition, classical):
    if condition is None:
        return True
    bits = classical[condition["register"]]
    value = (
        bits[condition["bit"]]
        if condition["bit"] is not None
        else sum(b << i for i, b in enumerate(bits))
    )
    return value == condition["value"]


def classical_snapshot(classical):
    """Full initialized memory; bit 0 is rightmost within each named register."""
    return {
        name: "".join(str(b) for b in reversed(bits))
        for name, bits in classical.items()
    }


def measured_bitstring(classical, written, order):
    """Project onto mapped destinations only; x means a conditional write was skipped."""
    return "".join(
        str(classical[r["register"]][r["bit"]])
        if (r["register"], r["bit"]) in written
        else "x"
        for r in order
    )

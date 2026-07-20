# Quantum Computing libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
QUANTUM_COMPUTING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "qiskit": {
        "description": "IBM SDK for quantum circuits, transpilation, and primitives",
        "category": "quantum_computing",
        "official_docs": "https://docs.quantum.ibm.com",
        "github": "https://github.com/Qiskit/qiskit",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "cirq": {
        "description": "Google framework for programming NISQ quantum circuits",
        "category": "quantum_computing",
        "official_docs": "https://quantumai.google/cirq",
        "github": "https://github.com/quantumlib/Cirq",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pennylane": {
        "description": "Differentiable quantum programming and quantum machine learning",
        "category": "quantum_computing",
        "official_docs": "https://docs.pennylane.ai",
        "github": "https://github.com/PennyLaneAI/pennylane",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "qutip": {
        "description": "Simulation of open quantum systems dynamics",
        "category": "quantum_computing",
        "official_docs": "https://qutip.readthedocs.io/en/stable",
        "github": "https://github.com/qutip/qutip",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "cuquantum": {
        "description": "NVIDIA GPU-accelerated quantum circuit simulation SDK",
        "category": "quantum_computing",
        "official_docs": "https://docs.nvidia.com/cuda/cuquantum",
        "github": "https://github.com/NVIDIA/cuQuantum",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "qulacs": {
        "description": "Fast quantum circuit simulator (C++/Python)",
        "category": "quantum_computing",
        "official_docs": "https://docs.qulacs.org",
        "github": "https://github.com/qulacs/qulacs",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}

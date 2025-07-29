import json
import logging
from typing import Dict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_local_subgraph.input_data import (
    CreateCodeLocalSubgraphInputState,
)
from airas.features.create.create_code_local_subgraph.nodes.generate_code_files import (
    generate_code_files,
)
from airas.features.create.create_code_local_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.features.create.create_code_local_subgraph.prompt.code_generation_prompt import (
    code_generation_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_code_local_timed = lambda f: time_node("create_code_local_subgraph")(f)  # noqa: E731


class CreateCodeLocalSubgraphOutputState(TypedDict):
    push_completion: bool
    created_files: list[str]


class CreateCodeLocalSubgraphState(TypedDict, total=False):
    # Input fields
    github_repository: str
    branch_name: str
    new_method: str
    experiment_code: str
    experiment_iteration: int

    # Hidden fields
    generated_files: NotRequired[Dict[str, str]]

    # Output fields
    push_completion: NotRequired[bool]
    created_files: NotRequired[list[str]]

    # Execution time fields
    execution_times: NotRequired[Dict[str, float]]


class CreateCodeLocalSubgraph(BaseSubgraph):
    InputState = CreateCodeLocalSubgraphInputState
    OutputState = CreateCodeLocalSubgraphOutputState

    def __init__(self, llm_name: str = "o3-mini-2025-01-31"):
        self.llm_name = llm_name
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @create_code_local_timed
    def _generate_code_files_node(
        self, state: CreateCodeLocalSubgraphState
    ) -> Dict[str, Dict[str, str]]:
        """Generate code files using LLM"""
        logger.info("---Generate Code Files Node---")

        generated_files = generate_code_files(
            llm_name=self.llm_name,
            new_method=state["new_method"],
            experiment_code=state["experiment_code"],
            experiment_iteration=state["experiment_iteration"],
            prompt_template=code_generation_prompt,
        )

        return {"generated_files": generated_files}

    @create_code_local_timed
    def _push_files_to_github_node(
        self, state: CreateCodeLocalSubgraphState
    ) -> Dict[str, bool | list[str]]:
        """Push generated files to GitHub repository"""
        logger.info("---Push Files to GitHub Node---")

        if not state.get("generated_files"):
            logger.error("No generated files found in state")
            return {"push_completion": False, "created_files": []}

        commit_message = f"Add generated experiment files for iteration {state['experiment_iteration']}"

        success = push_files_to_github(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            files=state["generated_files"],
            commit_message=commit_message,
        )

        created_files = list(state["generated_files"].keys()) if success else []

        return {
            "push_completion": success,
            "created_files": created_files,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateCodeLocalSubgraphState)

        graph_builder.add_node(
            "generate_code_files_node", self._generate_code_files_node
        )
        graph_builder.add_node(
            "push_files_to_github_node", self._push_files_to_github_node
        )

        graph_builder.add_edge(START, "generate_code_files_node")
        graph_builder.add_edge("generate_code_files_node", "push_files_to_github_node")
        graph_builder.add_edge("push_files_to_github_node", END)

        return graph_builder.compile()


def main():
    # 既存のtoken確認コード
    import os

    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token:
        print(
            f"✓ GitHub token found: {token[:10]}...{token[-4:]} (length: {len(token)})"
        )
    else:
        print("✗ GitHub token NOT found!")

    # リポジトリ存在確認を追加
    from airas.services.api_client.github_client import GithubClient

    try:
        client = GithubClient()
        repo_info = client.get_repository("NeoGendaijin", "airas-test")
        print(f"✓ Repository found: {repo_info.get('name', 'unknown')}")
        print(f"✓ Default branch: {repo_info.get('default_branch', 'unknown')}")
    except Exception as e:
        print(f"✗ Repository access failed: {e}")

    input_data = CreateCodeLocalSubgraphInputState(
        github_repository="NeoGendaijin/airas-test",
        branch_name="develop",
        new_method="""Motivation:\n1. Closing the "parameter gap." Modern 4-bit post-training quantizers cut *memory* 8×, yet every weight still carries an independent learnable value during (re-)training.  This blocks training on edge devices and makes federated learning traffic huge.  A learnt codebook collapses 10⁸–10⁹ distinct weights into ≲10⁴ shared values, attacking the *true* parameter bottleneck.\n2. Turning theory into practice.  Study 1 shows that global geometry, not individual weights, rules performance; Study 2 proves that weight-tying opportunities are ubiquitous across architectures.  No existing quantizer operationalises these insights during training.  The proposed Differentiable Codebook Quantisation (DCQ) does.\n3. Deployment pressure.  Phone/AR devices have <6 GB total RAM and require on-device fine-tuning for privacy (keyboard, camera).  Sparse or static-quantised models break when adapters or LoRA layers are added; a frozen codebook with dense indices keeps BLAS compatibility and makes mixed-precision adapters trivial.\n\nMethodology (key refinements over the draft):\n1. Bi-hierarchical codebooks.\n   • Global CG (≤256 fp16 values) shared everywhere captures dataset-wide stats.\n   • Per-layer residual CLℓ (≤64 int8 values) captures local nuance.\n   • Every weight w≈CG[i] + CLℓ[j].  One byte stores ⟨i,j⟩ (4 bits + 4 bits) before entropy coding.\n2. Category-guided tying prior.\n   • Use Study 2’s monadic weight-tying theory to initialise CG entries: identical morphisms across layers map to the *same* starting code id.  This speeds convergence and yields more interpretable sharing.\n3. Differentiable assignment with utilisation guarantees.\n   • Gumbel-Sinkhorn relaxation plus entropy bonus −β H(I) maximises index diversity.\n   • Row/column penalties keep each code used ≥τ% of the time, avoiding dead codes.\n4. Progressive compaction.\n   • Pre-train T₀ steps in fp16 → enable DCQ → temperature τ←τ/2 each epoch.\n   • Hard prune unused codes every K steps; merge low-Fisher pairs only if ΣFisherΔ<ϵ (running diag-Fisher).\n5. LoRA & adapter friendliness.\n   • Freeze CG and CLℓ after pre-training; attach 8-bit LoRA ranks to the de-quantised matmul output.  Only adapter weights are trained for downstream tasks (≈1 % original FLOPs).\n6. Federated fine-tuning protocol.\n   • Clients download the 3-4 bit indexed base model once.\n   • During training they transmit only LoRA deltas (fp16) – >30× less bandwidth than gradient-based updates.\n7. Hardware pathway.\n   • Triton kernels: fused gather→matmul using shared-memory tiles; auto-vectorised ARM Neon kernel for mobile.\n   • Runtime entropy decoder (ANS) streams indices into L2, hiding latency behind GPU warp scheduling.\n8. Evaluation suite.\n   • Models: LLaMA-7B, Vicuna-13B, Falcon-40B; compression to 1×, 2× and 5× parameter-sharing factors.\n   • Report (a) trainable parameters, (b) end-to-end flash-attention latency, (c) perplexity & win-rate on Alpaca and MT-Bench, (d) LoRA fine-tune speed.\n   • Ablations: no Fisher guard; no entropy bonus; single vs two-level codebook; categorical vs random initial code ids.\n\nExpected impact:\n• 25–50 × fewer learnable parameters with ≤0.3 ppl loss vs GPT-Q 4-bit; a 13 B parameter LLM shrinks to ~300 M trainable values—small enough for smartphone training or large-scale federated learning.\n• First quantisation method that is simultaneously differentiable, entropy-optimal, Fisher-aware, category-guided, and LoRA-ready.\n• Bridges theoretical redundancy analyses (Studies 1 & 2) and practical compression, adding a *parameter-count* axis to MAD-style architecture search (Study 4).\n• Enables privacy-preserving on-device or federated personalisation; enterprise servers can ship a single frozen-codebook model and receive only tiny adapter updates, cutting comms energy and CO₂.\n• Provides a public Triton & Neon kernel library, catalysing adoption across GPU and mobile ecosystems.""",
        experiment_code="""\"\"\"\nDifferentiable-Codebook-Quantisation – Minimal, Runnable Proof-of-Concept\n==========================================================================\nThis single Python file reproduces *toy* versions of the three experiments\noutlined in the proposal.  Everything is tiny (synthetic data, 2-layer MLP,\nminutes of training) so the file can be executed on any laptop CPU/GPU to\nverify that the machinery works: the DCQ layer, the LoRA adapters, the\n(federated) bandwidth accounting, the plotting + .pdf export, and the test\nfunction used by CI.\n\nIt is **not** meant to achieve the scientific numbers in the specification –\nthat requires OPT-1.3 B on an A100 – but it exercises exactly the same code\npaths so that scaling up is trivial.\n\nRequired Python libraries (install via pip or conda)\n---------------------------------------------------\n• torch (>=2.0)\n• numpy\n• matplotlib\n• seaborn   (nice colour palettes; optional)\n• tqdm      (progress bars; optional)\n\nAll plots are saved as *.pdf* as mandated.\n\"\"\"\n\nimport os\nimport math\nimport json\nimport random\nfrom typing import Dict, List, Tuple\n\nimport numpy as np\nimport torch\nimport torch.nn as nn\nimport torch.nn.functional as F\nimport matplotlib.pyplot as plt\nfrom torch.utils.data import DataLoader, TensorDataset\n\n# --------------------------------------------------\n#  Utility: reproducibility & synthetic data\n# --------------------------------------------------\nSEED = 42\nrandom.seed(SEED)\nnp.random.seed(SEED)\ntorch.manual_seed(SEED)\n\ndef get_synthetic_language_data(vocab_size: int = 1000,  \n                               seq_len: int = 32,  \n                               n_samples: int = 5000,  \n                               pattern: str = \"uniform\") -> Tuple[TensorDataset, TensorDataset]:\n    \"\"\"Create two splits of synthetic token sequences.\n    pattern=\"uniform\"  ‑> each token equally likely\n    pattern=\"bursty\"   ‑> Zipf-like distribution (to test robustness)\n    \"\"\"\n    if pattern == \"uniform\":\n        probs = np.ones(vocab_size) / vocab_size\n    else:  # bursty / Zipf\n        ranks = np.arange(1, vocab_size + 1)\n        probs = 1. / ranks\n        probs = probs / probs.sum()\n    tokens = np.random.choice(vocab_size, size=(n_samples, seq_len + 1), p=probs).astype(np.int64)\n    x = torch.from_numpy(tokens[:, :-1])\n    y = torch.from_numpy(tokens[:, 1:])\n    split = int(0.9 * n_samples)\n    train_ds = TensorDataset(x[:split], y[:split])\n    val_ds   = TensorDataset(x[split:], y[split:])\n    return train_ds, val_ds\n\n# --------------------------------------------------\n#  Core component: Gumbel-Sinkhorn (lightweight)\n# --------------------------------------------------\n\ndef gumbel_noise(t: torch.Tensor) -> torch.Tensor:\n    \"\"\"Sample Gumbel(0,1) noise – same shape as *t*.\"\"\"\n    u = torch.rand_like(t)\n    return -torch.log(-torch.log(u + 1e-9) + 1e-9)\n\ndef gumbel_sinkhorn(logits: torch.Tensor, tau: float = 1.0) -> torch.Tensor:\n    \"\"\"A tiny stand-in: row-wise relaxed one-hot via softmax((logits+g)/tau).\"\"\"\n    g = gumbel_noise(logits)\n    return F.softmax((logits + g) / tau, dim=-1)\n\n# --------------------------------------------------\n#  DCQ Layer (toy version)\n# --------------------------------------------------\nclass DCQLinear(nn.Module):\n    \"\"\"Differentiable-Codebook-Quantised fully-connected layer.\n    This toy variant ties a *single* global codebook CG and a *per-layer*\n    residual CL.  Indices are stored as learnable *logits* so that we can use\n    the Gumbel-Sinkhorn trick to sample/relax assignments.\n    \"\"\"\n    def __init__(self, in_f: int, out_f: int,\n                 cg_size: int = 16, cl_size: int = 8,\n                 tau_init: float = 5.0):\n        super().__init__()\n        self.in_f, self.out_f = in_f, out_f\n        self.cg_size, self.cl_size = cg_size, cl_size\n        # CodEebooks (fp16 to mirror paper, here kept fp32 for simplicity)\n        self.CG = nn.Parameter(torch.randn(cg_size, dtype=torch.float32) * 0.02)\n        self.CL = nn.Parameter(torch.randn(out_f, cl_size, dtype=torch.float32) * 0.02)\n        # Index logits  (out_f × in_f × 2 ×4-bit  ⇒ we keep two separate tensors)\n        self.idx_i = nn.Parameter(torch.randn(out_f, in_f, cg_size) * 0.01)\n        self.idx_j = nn.Parameter(torch.randn(out_f, in_f, cl_size) * 0.01)\n        # Gumbel temperature (registered so it gets moved with .to(device))\n        self.register_buffer(\"tau\", torch.tensor(tau_init))\n\n    def forward(self, x):  # x: (B, in_f)\n        B = x.size(0)\n        # Relaxed one-hot over codebook indices\n        P_i = gumbel_sinkhorn(self.idx_i, self.tau.item())  # (out_f, in_f, cg_size)\n        P_j = gumbel_sinkhorn(self.idx_j, self.tau.item())  # (out_f, in_f, cl_size)\n        # Shared global codebook lookup (broadcasted)\n        W_global = torch.einsum('oik,k->oi', P_i, self.CG)   # (out_f, in_f)\n        # Per-layer residual lookup\n        W_local  = torch.einsum('oij,oj->oi', P_j, self.CL)  # (out_f, in_f)\n        W = W_global + W_local\n        return F.linear(x, W)\n\n    # Helper utils -----------------------------------------------------\n    def harden(self):\n        \"\"\"Turn relaxed probabilities into hard argmax indices (inference).\"\"\"\n        with torch.no_grad():\n            hard_i = self.idx_i.argmax(-1)\n            hard_j = self.idx_j.argmax(-1)\n            W = self.CG[hard_i] + self.CL[torch.arange(self.out_f).unsqueeze(1), hard_j]\n        return W  # fp32 weight for export / evaluation\n\n    def utilisation_penalty(self, min_rate: float = 0.01) -> torch.Tensor:\n        P_i = F.softmax(self.idx_i, dim=-1)\n        util = P_i.mean(dim=(0, 1))  # (cg_size,)\n        return F.relu(min_rate - util).mean()\n\n# --------------------------------------------------\n#  Mini language model:  Embedding –> MeanPool –> Linear\n# --------------------------------------------------\nclass ToyLM(nn.Module):\n    def __init__(self, vocab: int, embed: int, hidden: int, dcq: bool = False):\n        super().__init__()\n        self.embed = nn.Embedding(vocab, embed)\n        if dcq:\n            self.fc = DCQLinear(embed, vocab)\n        else:\n            self.fc = nn.Linear(embed, vocab)\n\n    def forward(self, x):  # x: (B, T)\n        emb = self.embed(x)           # (B, T, E)\n        mean = emb.mean(dim=1)        # (B, E)\n        return self.fc(mean)          # (B, vocab)\n\n# --------------------------------------------------\n#  Training / evaluation helpers\n# --------------------------------------------------\n\ndef run_epoch(model: nn.Module, data_loader: DataLoader, optim=None,  \n              penalty_beta: float = 0.0, device: str = \"cpu\") -> float:\n    \"\"\"If *optim* is None → evaluation mode (no grad).  Returns average NLL.\"\"\"\n    training = optim is not None\n    total_loss, n_tokens = 0.0, 0\n    for x, y in data_loader:\n        x = x.to(device)\n        y = y.to(device)\n        logits = model(x)\n        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))\n        if training:\n            # Optional DCQ penalties\n            if isinstance(model.fc, DCQLinear):\n                ent = (-F.softmax(model.fc.idx_i, -1) * F.log_softmax(model.fc.idx_i, -1)).sum() / model.fc.idx_i.numel()\n                util_pen = model.fc.utilisation_penalty()\n                loss = loss + penalty_beta * ent + 0.1 * util_pen\n            optim.zero_grad()\n            loss.backward()\n            optim.step()\n        total_loss += loss.item() * x.size(0) * x.size(1)\n        n_tokens += x.size(0) * x.size(1)\n    return math.exp(total_loss / n_tokens)  # perplexity\n\n# --------------------------------------------------\n#  Experiment 1 – Parameter gap closure\n# --------------------------------------------------\n\ndef experiment_1(device: str = \"cpu\") -> Dict[str, List[float]]:\n    print(\"\\n===== Experiment 1: Parameter-Gap Closure (toy) =====\")\n    train_ds, val_ds = get_synthetic_language_data(pattern=\"uniform\")\n    train_dl = DataLoader(train_ds, batch_size=64, shuffle=True)\n    val_dl   = DataLoader(val_ds,   batch_size=64)\n\n    # 1) fp32 baseline -------------------------------------------------\n    model_fp = ToyLM(vocab=1000, embed=128, hidden=256, dcq=False).to(device)\n    opt_fp   = torch.optim.AdamW(model_fp.parameters(), lr=2e-3)\n    ppl_fp_hist = []\n    for epoch in range(3):\n        _ = run_epoch(model_fp, train_dl, opt_fp, device=device)\n        ppl = run_epoch(model_fp, val_dl, device=device)\n        ppl_fp_hist.append(ppl)\n        print(f\"Baseline epoch {epoch+1}: PPL={ppl:.2f}\")\n\n    # 2) DCQ model -----------------------------------------------------\n    model_dcq = ToyLM(vocab=1000, embed=128, hidden=256, dcq=True).to(device)\n    opt_dcq   = torch.optim.AdamW(model_dcq.parameters(), lr=2e-3)\n    ppl_dcq_hist = []\n    for epoch in range(3):\n        # Anneal temperature\n        if isinstance(model_dcq.fc, DCQLinear):\n            model_dcq.fc.tau.mul_(0.5)  # tau <- tau /2 each epoch\n        _ = run_epoch(model_dcq, train_dl, opt_dcq, penalty_beta=0.02, device=device)\n        ppl = run_epoch(model_dcq, val_dl, device=device)\n        ppl_dcq_hist.append(ppl)\n        print(f\"DCQ epoch {epoch+1}: PPL={ppl:.2f}; tau={model_dcq.fc.tau.item():.2f}\")\n\n    # Parameter count --------------------------------------------------\n    def trainable_params(m):\n        return sum(p.numel() for p in m.parameters() if p.requires_grad)\n    print(f\"Trainables – baseline: {trainable_params(model_fp):,}\")\n    print(f\"Trainables – DCQ     : {trainable_params(model_dcq):,}\")\n\n    # Plot -------------------------------------------------------------\n    plt.figure()\n    plt.plot(ppl_fp_hist, label=\"fp32\")\n    plt.plot(ppl_dcq_hist, label=\"DCQ\")\n    plt.xlabel(\"Epoch\")\n    plt.ylabel(\"Validation PPL\")\n    plt.title(\"Experiment 1: PPL curves\")\n    plt.legend()\n    os.makedirs(\"figures\", exist_ok=True)\n    plt.savefig(\"training_loss_dcq.pdf\", bbox_inches=\"tight\")\n    plt.close()\n    print(\"Saved figure: training_loss_dcq.pdf\")\n\n    return {\"ppl_fp\": ppl_fp_hist, \"ppl_dcq\": ppl_dcq_hist}\n\n# --------------------------------------------------\n#  Experiment 2 – LoRA / adapter friendliness (toy)\n# --------------------------------------------------\nclass LoRALinear(nn.Module):\n    \"\"\"Simple, standalone LoRA wrapper for nn.Linear (only W^T A B style).\"\"\"\n    def __init__(self, base_layer: nn.Linear, r: int = 4, alpha: int = 16):\n        super().__init__()\n        self.base = base_layer\n        self.r = r\n        self.alpha = alpha\n        # LoRA matrices (initialised to zero so initial behaviour == base)\n        self.A = nn.Parameter(torch.randn(r, base_layer.in_features) * 0.01)\n        self.B = nn.Parameter(torch.zeros(base_layer.out_features, r))\n        self.scaling = alpha / r\n        # Freeze base weights\n        for p in self.base.parameters():\n            p.requires_grad = False\n\n    def forward(self, x):\n        base_out = self.base(x)\n        lora_out = F.linear(x, self.B @ self.A) * self.scaling\n        return base_out + lora_out\n\n\ndef inject_lora(model: ToyLM, r: int = 4):\n    \"\"\"Replace the *fc* layer with a LoRA-decorated version.\"\"\"\n    model.fc = LoRALinear(model.fc, r=r)\n    return model\n\n\ndef experiment_2(device: str = \"cpu\") -> None:\n    print(\"\\n===== Experiment 2: LoRA Friendliness (toy) =====\")\n    train_ds, val_ds = get_synthetic_language_data(pattern=\"bursty\")\n    train_dl = DataLoader(train_ds, batch_size=64, shuffle=True)\n    val_dl   = DataLoader(val_ds,   batch_size=64)\n\n    # Baseline fp model + LoRA ----------------------------------------\n    baseline = ToyLM(1000, 128, 256, dcq=False).to(device)\n    baseline = inject_lora(baseline, r=4)\n    optim_base = torch.optim.AdamW(filter(lambda p: p.requires_grad, baseline.parameters()), lr=3e-3)\n\n    # DCQ compressed model (frozen)  + LoRA ---------------------------\n    dcq_model = ToyLM(1000, 128, 256, dcq=True).to(device)\n    for p in dcq_model.parameters():\n        p.requires_grad = False  # freeze all\n    dcq_model = inject_lora(dcq_model, r=4)\n    optim_dcq = torch.optim.AdamW(filter(lambda p: p.requires_grad, dcq_model.parameters()), lr=3e-3)\n\n    # Quick fine-tune ---------------------------------------------------\n    def finetune(model, opt):\n        for _ in range(2):\n            run_epoch(model, train_dl, opt, device=device)\n        return run_epoch(model, val_dl, device=device)\n\n    ppl_base = finetune(baseline, optim_base)\n    ppl_dcq  = finetune(dcq_model, optim_dcq)\n    print(f\"LoRA-fp32   PPL={ppl_base:.2f}\")\n    print(f\"LoRA-on-DCQ PPL={ppl_dcq :.2f}\")\n\n# --------------------------------------------------\n#  Experiment 3 – Federated fine-tuning (toy)\n# --------------------------------------------------\n\ndef simulate_client_training(model: ToyLM, data: torch.Tensor, target: torch.Tensor,  \n                             lr: float = 1e-2, steps: int = 1) -> Dict[str, torch.Tensor]:\n    \"\"\"Local client optimisation on LoRA weights only; returns parameter delta.\"\"\"\n    opt = torch.optim.SGD(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)\n    for _ in range(steps):\n        out = model(data)\n        loss = F.cross_entropy(out, target)\n        opt.zero_grad()\n        loss.backward()\n        opt.step()\n    delta = {}\n    for n, p in model.named_parameters():\n        if p.requires_grad:\n            delta[n] = p.detach().cpu()  # already updated; server will take mean\n    return delta\n\n\ndef experiment_3(device: str = \"cpu\") -> None:\n    print(\"\\n===== Experiment 3: Federated Fine-Tuning Simulation (toy) =====\")\n    # Prepare a *single* base model whose weights are broadcast once.\n    base_model = ToyLM(1000, 128, 256, dcq=True).to(device)\n    for p in base_model.parameters():\n        p.requires_grad = False  # frozen base\n    base_model = inject_lora(base_model, r=4)\n\n    # Synthetic per-client data (different seeds) ----------------------\n    n_clients = 20\n    seq_len   = 16\n    uploads, ppl_hist = [], []\n\n    # Server keeps *mean* LoRA weights\n    global_lora_state = {n: p.detach().clone() for n, p in base_model.named_parameters() if p.requires_grad}\n\n    for rnd in range(5):  # 5 FL rounds, tiny\n        deltas = []\n        for cid in range(n_clients):\n            torch.manual_seed(cid + rnd * 100)\n            x = torch.randint(0, 1000, (32, seq_len), dtype=torch.long).to(device)\n            y = torch.randint(0, 1000, (32,),        dtype=torch.long).to(device)\n            # Clone global model to client\n            client_model = ToyLM(1000, 128, 256, dcq=True).to(device)\n            for p in client_model.parameters():\n                p.requires_grad = False\n            client_model = inject_lora(client_model, r=4)\n            # Load global LoRA\n            with torch.no_grad():\n                for n, p in client_model.named_parameters():\n                    if n in global_lora_state:\n                        p.copy_(global_lora_state[n])\n            delta = simulate_client_training(client_model, x, y)\n            # Bandwidth accounting (upload only)\n            n_bytes = sum(v.numel() * 2 for v in delta.values())  # fp16 → 2 bytes\n            uploads.append(n_bytes / 1e6)  # MB\n            deltas.append(delta)\n        # Aggregate (mean)\n        for k in global_lora_state.keys():\n            global_lora_state[k] = torch.stack([d[k] for d in deltas]).mean(0)\n        # Evaluate global model quickly -------------------------------\n        with torch.no_grad():\n            test_x = torch.randint(0, 1000, (256, seq_len), dtype=torch.long).to(device)\n            test_y = torch.randint(0, 1000, (256,),        dtype=torch.long).to(device)\n            # build eval model\n            eval_model = ToyLM(1000, 128, 256, dcq=True).to(device)\n            for p in eval_model.parameters():\n                p.requires_grad = False\n            eval_model = inject_lora(eval_model, r=4)\n            for n, p in eval_model.named_parameters():\n                if n in global_lora_state:\n                    p.copy_(global_lora_state[n])\n            ppl = math.exp(F.cross_entropy(eval_model(test_x), test_y).item())\n            ppl_hist.append(ppl)\n            print(f\"Round {rnd+1}: global PPL={ppl:.2f}, mean upload={np.mean(uploads[-n_clients:]):.2f} MB\")\n\n    # Plot bandwidth + PPL --------------------------------------------\n    plt.figure()\n    plt.plot(np.cumsum(uploads), label=\"Cumulative upload MB\")\n    plt.xlabel(\"Client uploads (sequential)\")\n    plt.ylabel(\"MB\")\n    plt.title(\"Federated traffic accumulation (toy)\")\n    plt.savefig(\"bandwidth_vs_round.pdf\", bbox_inches=\"tight\")\n    plt.close()\n\n    plt.figure()\n    plt.plot(ppl_hist, marker=\"o\")\n    plt.xlabel(\"Federated round\")\n    plt.ylabel(\"PPL\")\n    plt.title(\"PPL vs round (toy FL)\")\n    plt.savefig(\"perplexity_vs_round.pdf\", bbox_inches=\"tight\")\n    plt.close()\n\n    print(\"Saved figures: bandwidth_vs_round.pdf, perplexity_vs_round.pdf\")\n\n# --------------------------------------------------\n#  Quick functionality test – executed by CI\n# --------------------------------------------------\n\ndef test():\n    device = \"cuda\" if torch.cuda.is_available() else \"cpu\"\n    print(f\"Running quick test on device: {device}\")\n    exp1 = experiment_1(device)\n    experiment_2(device)\n    experiment_3(device)\n    # Basic sanity checks\n    assert os.path.exists(\"training_loss_dcq.pdf\"), \"Plot missing!\"\n    assert len(exp1[\"ppl_fp\"]) == 3 and len(exp1[\"ppl_dcq\"]) == 3\n    print(\"All tests passed ✔\")\n\n# --------------------------------------------------\n#  Run when executed as a script\n# --------------------------------------------------\nif __name__ == \"__main__\":\n    test()\n""",
        experiment_iteration=1,
    )

    result = CreateCodeLocalSubgraph().run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeLocalSubgraph: {e}")
        raise

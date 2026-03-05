import { Drawer } from "@/ui";

const mockPythonCode = `import torch
import torch.nn as nn
from transformers import BertModel, BertConfig

class SparseAttentionBert(nn.Module):
    """BERT model with configurable sparse attention."""

    def __init__(self, config: BertConfig, attention_type: str = "full",
                 top_k: int = 64, local_window: int = 64, global_tokens: int = 16):
        super().__init__()
        self.bert = BertModel(config)
        self.attention_type = attention_type
        self.top_k = top_k
        self.local_window = local_window
        self.global_tokens = global_tokens
        self.classifier = nn.Linear(config.hidden_size, 2)

    def sparse_attention(self, attention_scores, attention_mask):
        if self.attention_type == "top_k_sparse":
            top_k_values, _ = torch.topk(attention_scores, self.top_k, dim=-1)
            threshold = top_k_values[..., -1].unsqueeze(-1)
            mask = attention_scores >= threshold
            attention_scores = attention_scores.masked_fill(~mask, float('-inf'))
        elif self.attention_type == "local_global":
            seq_len = attention_scores.size(-1)
            local_mask = torch.ones(seq_len, seq_len, device=attention_scores.device)
            for i in range(seq_len):
                start = max(0, i - self.local_window // 2)
                end = min(seq_len, i + self.local_window // 2)
                local_mask[i, start:end] = 0
            local_mask[:, :self.global_tokens] = 0
            local_mask[:self.global_tokens, :] = 0
            attention_scores = attention_scores.masked_fill(
                local_mask.bool().unsqueeze(0).unsqueeze(0), float('-inf')
            )
        return attention_scores

    def forward(self, input_ids, attention_mask=None):
        outputs = self.bert(input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        logits = self.classifier(pooled_output)
        return logits
`;

interface CodeEditorModalProps {
  open: boolean;
  onClose: () => void;
  githubUrl: string;
}

export function CodeEditorModal({ open, onClose, githubUrl }: CodeEditorModalProps) {
  return (
    <Drawer open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <Drawer.Content>
        <div className="flex flex-col h-full w-[640px]">
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <div>
              <h2 className="text-base font-semibold text-foreground">コードプレビュー</h2>
              <a
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-brand-600 hover:underline"
              >
                GitHubで開く
              </a>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              閉じる
            </button>
          </div>
          <div className="flex-1 overflow-auto p-6">
            <div className="rounded-md bg-neutral-900 p-4 overflow-x-auto">
              <pre className="text-xs text-neutral-100 font-mono whitespace-pre">
                {mockPythonCode}
              </pre>
            </div>
          </div>
        </div>
      </Drawer.Content>
    </Drawer>
  );
}

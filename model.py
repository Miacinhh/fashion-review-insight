"""Inference matching the five-head ViSoBERT model in the group's notebook."""

import re
import unicodedata
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from torch import nn
from transformers import AutoModel, AutoTokenizer

BASE_MODEL = "uitnlp/visobert"
ASPECTS = ["Chất liệu", "Kiểu dáng", "Kích cỡ", "Giá cả", "Dịch vụ"]
LABELS = ["Không đề cập", "Tiêu cực", "Trung tính / pha trộn", "Tích cực"]
MAX_LENGTH = 192


def clean_text(value: str) -> str:
    text = unicodedata.normalize("NFC", str(value))
    text = text.replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", text).strip()


class VisoBERTMultiAspect(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(BASE_MODEL, add_pooling_layer=False)
        self.dropout = nn.Dropout(0.1)
        self.heads = nn.ModuleList(
            [nn.Linear(self.encoder.config.hidden_size, 4) for _ in ASPECTS]
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_vector = self.dropout(outputs.last_hidden_state[:, 0, :])
        return torch.stack([head(cls_vector) for head in self.heads], dim=1)


def load_model(repo_id: str = "", token: str | None = None):
    local = Path(__file__).parent / "best_visobert_multiaspect.pt"
    if local.is_file():
        checkpoint = local
    elif repo_id:
        checkpoint = Path(
            hf_hub_download(repo_id=repo_id, filename=local.name, token=token)
        )
    else:
        raise FileNotFoundError("Chưa cấu hình MODEL_REPO_ID hoặc file checkpoint cục bộ.")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=False)
    model = VisoBERTMultiAspect()
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval()
    return tokenizer, model


def predict(texts: list[str], tokenizer, model, batch_size: int = 8):
    """Return arrays shaped (number of reviews, five aspects)."""
    ids, confidences = [], []
    with torch.inference_mode():
        for start in range(0, len(texts), batch_size):
            chunk = [clean_text(x) for x in texts[start : start + batch_size]]
            tokens = tokenizer(
                chunk, return_tensors="pt", padding=True,
                truncation=True, max_length=MAX_LENGTH,
            )
            logits = model(
                input_ids=tokens["input_ids"],
                attention_mask=tokens["attention_mask"],
            )
            probabilities = logits.softmax(dim=-1)
            ids.append(probabilities.argmax(dim=-1).numpy())
            confidences.append(probabilities.max(dim=-1).values.numpy())
    if not ids:
        return np.empty((0, len(ASPECTS)), dtype=int), np.empty((0, len(ASPECTS)))
    return np.concatenate(ids), np.concatenate(confidences)

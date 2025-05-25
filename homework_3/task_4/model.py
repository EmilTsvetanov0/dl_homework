import torch
from torch import nn
from transformers import AutoModel

import torch.nn.functional as F

from homework_3.task_4.config import RetrievalPipelineConfig


class RetrievalModel(nn.Module):
    def __init__(self, cfg: RetrievalPipelineConfig):
        super().__init__()
        self._base_model = AutoModel.from_pretrained(cfg.base_model)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self._base_model(input_ids=input_ids, attention_mask=attention_mask)
        return F.normalize(outputs.pooler_output, dim=-1)
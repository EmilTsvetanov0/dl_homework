from typing import Any

import torch
import torchmetrics
from torch import nn

from homework_3.task_4.config import RetrievalPipelineConfig
from homework_3.task_4.trainer import Trainable


class ContrastiveTrainable(Trainable):
    def __init__(self, config: RetrievalPipelineConfig):
        self._config = config
        self._loss_fn = nn.CosineEmbeddingLoss(margin=config.similarity_margin)

    def forward_pass(self, model: nn.Module, model_inputs) -> tuple[torch.Tensor, Any]:
        emb_pos = model(model_inputs['positive']['input_ids'], model_inputs['positive']['attention_mask'])
        emb_neg = model(model_inputs['negative']['input_ids'], model_inputs['negative']['attention_mask'])
        emb_anchor = model(model_inputs['anchor']['input_ids'], model_inputs['anchor']['attention_mask'])

        device = emb_anchor.device
        label_pos = torch.ones(emb_anchor.size(0), device=device)
        label_neg = -torch.ones(emb_anchor.size(0), device=device)

        loss_pos = self._loss_fn(emb_anchor, emb_pos, label_pos)
        loss_neg = self._loss_fn(emb_anchor, emb_neg, label_neg)
        loss = 0.5 * (loss_pos + loss_neg)

        return loss, {'loss': loss}

    def create_metrics(self) -> dict[str, torchmetrics.Metric]:
        return {
            'loss': torchmetrics.MeanMetric()
        }

    def update_metrics(self, model_outputs, metrics: dict[str, torchmetrics.Metric]):
        metrics['loss'].update(model_outputs['loss'])
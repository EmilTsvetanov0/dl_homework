from typing import Any

import torch
import torchmetrics
from torch import nn
from torch.nn import TripletMarginLoss

from homework_3.task_4.config import RetrievalPipelineConfig
from homework_3.task_4.trainer import Trainable


class RetrievalTrainable(Trainable):
    def __init__(self, config: RetrievalPipelineConfig):
        self._config = config
        self._loss = TripletMarginLoss(margin=config.similarity_margin)

    def forward_pass(self, model: nn.Module, model_inputs) -> tuple[torch.Tensor, Any]:
        vectors_positive = model(model_inputs['positive']['input_ids'], model_inputs['positive']['attention_mask'])
        vectors_negative = model(model_inputs['negative']['input_ids'], model_inputs['negative']['attention_mask'])
        vectors_anchor = model(model_inputs['anchor']['input_ids'], model_inputs['anchor']['attention_mask'])
        loss = self._loss(vectors_anchor, vectors_positive, vectors_negative)
        return loss, {
            'loss': loss
        }

    def create_metrics(self) -> dict[str, torchmetrics.Metric]:
        return {
            'loss': torchmetrics.MeanMetric()
        }

    def update_metrics(self, model_outputs, metrics: dict[str, torchmetrics.Metric]):
        metrics['loss'].update(model_outputs['loss'])
import abc
import time
from pathlib import Path
from typing import Any

import bitsandbytes.optim.adam
import torch
import torchmetrics
import transformers
from accelerate import Accelerator, DataLoaderConfiguration
from accelerate.utils import set_seed
from torch import nn
from torch.optim import Optimizer, SGD, Adam, AdamW
from torch.optim.lr_scheduler import LRScheduler
from torch.optim.optimizer import ParamsT
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from homework_3.task_4.config import TrainerConfig, SGDConfig, AdamConfig, AdamWConfig, ConstantSchedulerConfig, \
    LinearWarmupSchedulerConfig, LowPrecision, PrecisionConfig, AdamW8BitConfig


def _convert_precision(x: nn.Module | torch.Tensor, config: PrecisionConfig) -> nn.Module | torch.Tensor:
    if config.enable_amp:
        return x

    if isinstance(x, torch.Tensor) and x.dtype not in {torch.float32}:
        return x

    match config.low_precision:
        case LowPrecision.no:
            return x
        case LowPrecision.fp16:
            return x.half()
        case LowPrecision.bf16:
            return x.to(torch.bfloat16)
        case _:
            raise NotImplementedError()


def _convert_minibatch(minibatch, precision_config: PrecisionConfig):
    if isinstance(minibatch, dict):
        return {k: _convert_minibatch(v, precision_config) for k, v in minibatch.items()}
    elif isinstance(minibatch, list):
        return [_convert_minibatch(x, precision_config) for x in minibatch]
    elif isinstance(minibatch, torch.Tensor):
        return _convert_precision(minibatch, precision_config)
    else:
        return minibatch


class Trainable(abc.ABC):
    @abc.abstractmethod
    def forward_pass(self, model: nn.Module, model_inputs) -> tuple[torch.Tensor, Any]:
        ...

    @abc.abstractmethod
    def create_metrics(self) -> dict[str, torchmetrics.Metric]:
        ...

    @abc.abstractmethod
    def update_metrics(self, model_outputs, metrics: dict[str, torchmetrics.Metric]):
        ...


class Trainer:
    def __init__(self, config: TrainerConfig, model: nn.Module, trainable: Trainable,
                 collator):
        self._config = config
        self._model = model
        self._trainable = trainable
        self._collator = collator

    def _create_optimizer(self, params: ParamsT) -> Optimizer:
        match self._config.optimizer:
            case SGDConfig():
                return SGD(params, lr=self._config.optimizer.learning_rate)
            case AdamConfig():
                return Adam(params, lr=self._config.optimizer.learning_rate)
            case AdamWConfig():
                return AdamW(
                    params,
                    lr=self._config.optimizer.learning_rate,
                    weight_decay=self._config.optimizer.weight_decay
                )
            case AdamW8BitConfig():
                return bitsandbytes.optim.adam.Adam8bit(
                    params,
                    lr=self._config.optimizer.learning_rate,
                    weight_decay=self._config.optimizer.weight_decay
                )
            case _:
                raise ValueError(f'Optimizer {self._config.optimizer} is not supported')

    def _create_scheduler(self, optimizer: Optimizer, num_total_steps: int) -> LRScheduler:
        match self._config.scheduler:
            case ConstantSchedulerConfig():
                return transformers.get_constant_schedule(optimizer)
            case LinearWarmupSchedulerConfig():
                return transformers.get_linear_schedule_with_warmup(
                    optimizer,
                    num_warmup_steps=int(num_total_steps * self._config.scheduler.warmup_steps_proportion),
                    num_training_steps=num_total_steps
                )
            case _:
                raise ValueError(f'Scheduler {self._config.scheduler} is not supported')

    def _create_dataloader(
            self,
            dataset: Dataset,
            for_training: bool
    ):
        if for_training:
            shuffle = self._config.shuffle_train_dataset
        else:
            shuffle = False

        return DataLoader(
            dataset,
            batch_size=self._config.minibatch_size,
            shuffle=shuffle,
            num_workers=self._config.num_workers,
            collate_fn=self._collator,
            pin_memory=True,
            persistent_workers=True
        )

    def _compute_and_log_metrics(
            self,
            prefix: str,
            accelerator: Accelerator,
            metrics: dict[str, torchmetrics.Metric],
            current_step: int
    ):
        metric_values = {k: v.compute().item() for k, v in metrics.items()}
        metric_values = {f'{prefix}{k}': v for k, v in metric_values.items()}
        accelerator.log(metric_values, step=current_step)

    def _train_loop_iter(
            self,
            epoch_i: int,
            dataloader: DataLoader,
            dataloader_eval: DataLoader,
            model: nn.Module,
            optimizer: Optimizer,
            scheduler: LRScheduler,
            accelerator: Accelerator,
            pbar: tqdm
    ):
        model.train()
        metrics = None

        for i, minibatch in enumerate(dataloader):
            minibatch = _convert_minibatch(minibatch, self._config.precision)
            current_global_step = epoch_i * len(dataloader) + i
            current_global_optimizer_step = current_global_step // self._config.gradient_accumulation_steps
            if accelerator.sync_gradients and current_global_optimizer_step % self._config.log_steps == 0:
                if metrics is not None:
                    self._compute_and_log_metrics(
                        prefix='step/train/',
                        accelerator=accelerator,
                        metrics=metrics,
                        current_step=current_global_optimizer_step
                    )

                metrics = self._create_metrics(accelerator)

            with accelerator.accumulate():
                t0_forward = time.time()
                with accelerator.autocast():
                    loss_value, outputs = self._trainable.forward_pass(model, minibatch)
                t1_forward = time.time()
                metrics['run_time_forward'].update(t1_forward - t0_forward)

                self._trainable.update_metrics(outputs, metrics)

                t0_backward = time.time()
                accelerator.backward(loss_value)
                t1_backward = time.time()
                metrics['run_time_backward'].update(t1_backward - t0_backward)

                t0_opt_step = time.time()
                optimizer.step()
                t1_opt_step = time.time()
                metrics['run_time_optimizer'].update(t1_opt_step - t0_opt_step)

                scheduler.step()
                optimizer.zero_grad()

            if accelerator.sync_gradients and \
                    current_global_optimizer_step != 0 and \
                    current_global_optimizer_step % self._config.eval_steps == 0:
                self._eval_loop_iter(dataloader_eval, model, accelerator, current_global_optimizer_step)
            if accelerator.sync_gradients and current_global_optimizer_step != 0 and current_global_optimizer_step % self._config.save_steps == 0:
                accelerator.save_model(model, Path(self._config.project_dir) / f'save-{current_global_optimizer_step}')
            pbar.update(1)

    def _create_metrics(self, accelerator: Accelerator):
        metrics = self._trainable.create_metrics()
        metrics = {k: v.to(accelerator.device) for k, v in metrics.items()}

        default_metrics = self._create_default_metrics(accelerator)

        return {**metrics, **default_metrics}

    def _create_default_metrics(self, accelerator: Accelerator):
        metric_run_time_forward = torchmetrics.MeanMetric().to(accelerator.device)
        metric_run_time_backward = torchmetrics.MeanMetric().to(accelerator.device)
        return {
            'run_time_forward': metric_run_time_forward,
            'run_time_backward': metric_run_time_backward,
            'run_time_optimizer': torchmetrics.MeanMetric().to(accelerator.device)
        }

    def _eval_loop_iter(
            self,
            dataloader: DataLoader,
            model: nn.Module,
            accelerator: Accelerator,
            current_iter: int
    ):
        with torch.no_grad():
            model.eval()

            metrics = self._create_metrics(accelerator)

            for minibatch in dataloader:
                loss_value, outputs = self._trainable.forward_pass(model, minibatch)
                self._trainable.update_metrics(outputs, metrics)

            self._compute_and_log_metrics(
                prefix='step/eval/',
                accelerator=accelerator,
                metrics=metrics,
                current_step=current_iter
            )

            model.train()

    def _enable_tf32(self):
        torch.backends.cuda.matmul.allow_tf32 = self._config.precision.enable_tf32
        torch.backends.cudnn.allow_tf32 = self._config.precision.enable_tf32

    def _perform_low_casting(self, model: nn.Module) -> nn.Module:
        return _convert_precision(model, self._config.precision)

    def train(self, train_dataset: Dataset, val_dataset: Dataset):
        set_seed(self._config.seed)
        self._enable_tf32()

        train_dataloader = self._create_dataloader(train_dataset, for_training=True)
        val_dataloader = self._create_dataloader(val_dataset, for_training=False)
        amp_precision = self._config.precision.low_precision if self._config.precision.enable_amp else None
        accel = Accelerator(
            gradient_accumulation_steps=self._config.gradient_accumulation_steps,
            dataloader_config=DataLoaderConfiguration(
                use_stateful_dataloader=self._config.use_stateful_dataloader
            ),
            project_dir=self._config.project_dir,
            log_with=self._config.log_with,
            mixed_precision=amp_precision
        )
        accel.init_trackers(
            self._config.experiment_name,
            config={
                'lr': self._config.optimizer.learning_rate,
            }
        )
        train_dataloader, val_dataloader = accel.prepare(train_dataloader, val_dataloader)
        num_total_steps = len(train_dataloader) * self._config.num_epochs
        self._model = self._perform_low_casting(self._model)
        optimizer = self._create_optimizer(self._model.parameters())
        scheduler = self._create_scheduler(optimizer, num_total_steps=num_total_steps)
        model, optimizer, scheduler = accel.prepare(self._model, optimizer, scheduler)
        with tqdm(total=self._config.num_epochs * len(train_dataloader)) as pbar:
            for epoch in range(self._config.num_epochs):
                self._train_loop_iter(
                    dataloader=train_dataloader,
                    dataloader_eval=val_dataloader,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    accelerator=accel,
                    epoch_i=epoch,
                    pbar=pbar
                )
        accel.end_training()
from enum import StrEnum
from typing import Literal, Annotated

from pydantic import BaseModel, Field

class LinearWarmupSchedulerConfig(BaseModel):
    schedule: Literal['linear_warmup'] = 'linear_warmup'
    warmup_steps_proportion: float


class ConstantSchedulerConfig(BaseModel):
    schedule: Literal['constant'] = 'constant'

AnySchedulerConfig = Annotated[LinearWarmupSchedulerConfig | ConstantSchedulerConfig, Field(discriminator='schedule')]



class BaseOptimizerConfig(BaseModel):
    learning_rate: float

class AdamConfig(BaseOptimizerConfig):
    optimizer: Literal['adam'] = 'adam'


class AdamWConfig(BaseOptimizerConfig):
    optimizer: Literal['adamw'] = 'adamw'

    weight_decay: float


class AdamW8BitConfig(BaseOptimizerConfig):
    optimizer: Literal['adamw_8bit'] = 'adamw_8bit'

    weight_decay: float


class SGDConfig(BaseOptimizerConfig):
    optimizer: Literal['sgd'] = 'sgd'

AnyOptimizerConfig = Annotated[AdamConfig | AdamWConfig | SGDConfig | AdamW8BitConfig, Field(discriminator='optimizer')]



class LowPrecision(StrEnum):
    no = 'no'
    fp16 = 'fp16'
    bf16 = 'bf16'

class PrecisionConfig(BaseModel):
    enable_tf32: bool = False
    low_precision: LowPrecision = LowPrecision.no
    enable_amp: bool = False

class TrainerConfig(BaseModel):
    use_stateful_dataloader: bool = True
    num_epochs: int
    gradient_accumulation_steps: int
    project_dir: str
    log_steps: int
    eval_steps: int
    save_steps: int
    experiment_name: str
    log_with: str
    minibatch_size: int
    shuffle_train_dataset: bool
    num_workers: int
    seed: int
    precision: PrecisionConfig = Field(default_factory=PrecisionConfig)

    optimizer: AnyOptimizerConfig
    scheduler: AnySchedulerConfig


class RetrievalPipelineConfig(BaseModel):
    trainer: TrainerConfig
    max_length: int
    base_model: str
    dataset: str
    query_prefix: str
    document_prefix: str
    similarity_margin: float
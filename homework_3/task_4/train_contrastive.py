from pathlib import Path

import click

from homework_3.task_4.config import RetrievalPipelineConfig
from homework_3.task_4.data import RetrievalCollator, load_data
from homework_3.task_4.model import RetrievalModel
from homework_3.task_4.trainable_contrastive import ContrastiveTrainable
from homework_3.task_4.trainer import Trainer




@click.command()
@click.option('--config-path', type=Path, required=True)
def main(config_path: Path):
    config = RetrievalPipelineConfig.model_validate_json(config_path.read_text(encoding='utf-8'))
    model = RetrievalModel(config)
    trainable = ContrastiveTrainable(config)
    collator = RetrievalCollator()
    dataset_train, dataset_test = load_data(config, test_mode=False)
    trainer = Trainer(config.trainer, model, trainable, collator)
    trainer.train(dataset_train, dataset_test)


if __name__ == '__main__':
    main()
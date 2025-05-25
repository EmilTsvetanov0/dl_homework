from pathlib import Path
import click
import safetensors
import torch
from accelerate import Accelerator
from torch.utils.data import DataLoader
from sklearn.metrics.pairwise import cosine_similarity

from homework_3.task_4.config import RetrievalPipelineConfig
from homework_3.task_4.data import load_data, RetrievalCollator
from homework_3.task_4.model import RetrievalModel

from homework_3.task_1.metrics import recall_at_k, mrr

@click.command()
@click.option('--config-path', type=Path, required=True)
@click.option('--model-path', type=Path, required=True)
def main(config_path: Path, model_path: Path):
    accel = Accelerator()
    cfg = RetrievalPipelineConfig.model_validate_json(
        config_path.read_text(encoding='utf-8')
    )

    model = RetrievalModel(cfg).eval()
    safetensors.torch.load_model(model, model_path)

    test_ds = load_data(cfg, test_mode=True)
    loader = DataLoader(
        test_ds,
        shuffle=False,
        batch_size=cfg.trainer.minibatch_size,
        collate_fn=RetrievalCollator(),
        pin_memory=True
    )
    model, loader = accel.prepare(model, loader)

    all_q, all_d = [], []
    for batch in loader:
        q = model(batch['positive']['input_ids'], batch['positive']['attention_mask'])
        d = model(batch['anchor']['input_ids'],  batch['anchor']['attention_mask'])
        all_q.append(q)
        all_d.append(d)
    q_vecs = torch.cat(all_q).cpu().numpy()
    d_vecs = torch.cat(all_d).cpu().numpy()
    sim = cosine_similarity(q_vecs, d_vecs)
    preds = sim.argsort(axis=1)[:, ::-1].tolist()
    targets = list(range(len(preds)))
    results = {'mrr': mrr(targets, preds)}
    for k in (1, 3, 10):
        results[f'recall@{k}'] = recall_at_k(targets, preds, k)
    print("Evaluation results:", results)

if __name__ == '__main__':
    main()
# e5_baseline.py

from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch

import homework_3.config as config
from homework_3.task_1.metrics import recall_at_k, mrr
from homework_3.data_loader import load_nq_dataset

top_k_test_values: List[int] = [1, 3, 10]

def run_e5(
    test_queries: List[str],
    test_docs: List[str],
    model_name: str = config.E5_MODEL_NAME,
    batch_size: int = config.E5_BATCH_SIZE,
) -> Dict[str, float]:
    """
    1) Загружаем pretrained SentenceTransformer (E5)
    2) Кодируем документы и запросы
    3) cosine_similarity(query_emb, doc_emb)
    4) Считаем Recall@k и MRR
    """

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")


    print("Model initialization")
    model = SentenceTransformer(model_name).to(device)

    print("Vectorization initialization")
    # Векторизуем
    doc_embs   = model.encode(test_docs,   convert_to_numpy=True,
                               batch_size=batch_size, show_progress_bar=True)
    query_embs = model.encode(test_queries, convert_to_numpy=True,
                               batch_size=batch_size, show_progress_bar=True)


    print("Cosine similarity")
    sim = cosine_similarity(query_embs, doc_embs)
    predictions = sim.argsort(axis=1)[:, ::-1].tolist()
    targets = list(range(len(test_docs)))

    print("Recall@k")
    results = { "mrr": mrr(targets, predictions) }
    for k in top_k_test_values:
        results[f"recall@{k}"] = recall_at_k(targets, predictions, k)
    return results


def main():
    print("Загрузка и сплит датасета")
    train_q, train_d, test_q, test_d = load_nq_dataset(
        config.DATASET_NAME, config.TEST_SIZE, config.SEED
    )
    train_d = train_d[:40000]
    test_d = test_d[:8000]
    train_q = train_q[:40000]
    test_q = test_q[:8000]
    print(f"  train: {len(train_d)} примеров, test: {len(test_d)} примеров\n")

    print("E5 baseline")
    e5_res = run_e5(test_q, test_d)
    for k, v in e5_res.items():
        print(f"   {k}: {v:.4f}")
    print()

if __name__ == "__main__":
    main()

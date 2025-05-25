from typing import List, Dict
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

import homework_3.config as config
from homework_3.task_1.metrics import recall_at_k, mrr
from homework_3.data_loader import load_nq_dataset

top_k_test_values: List[int] = [1, 3, 10]

# CLS токен
def encode_texts(
    texts: List[str],
    tokenizer: AutoTokenizer,
    model: AutoModel,
    device: torch.device,
    batch_size: int = 32,
) -> torch.Tensor:
    model.eval()
    embeddings = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(device)

            outputs = model(**encoded)
            emb = outputs.pooler_output
            emb = F.normalize(emb, p=2, dim=1)
            embeddings.append(emb.cpu())
    return torch.cat(embeddings, dim=0).numpy()


def run_e5(
    test_queries: List[str],
    test_docs: List[str],
    model_name: str = config.E5_MODEL_NAME,
    batch_size: int = config.E5_BATCH_SIZE,
) -> Dict[str, float]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    print("Loading tokenizer and model")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)

    print("Encoding documents")
    doc_embs = encode_texts(test_docs, tokenizer, model, device, batch_size=batch_size)

    print("Encoding queries")
    query_embs = encode_texts(test_queries, tokenizer, model, device, batch_size=batch_size)

    print("Computing cosine similarity")
    sim = cosine_similarity(query_embs, doc_embs)

    predictions = sim.argsort(axis=1)[:, ::-1].tolist()
    targets = list(range(len(test_docs)))

    print("Calculating Recall@k and MRR")
    results = {"mrr": mrr(targets, predictions)}
    for k in (1, 3, 10):
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

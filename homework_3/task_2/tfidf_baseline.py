from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from homework_3.task_1.metrics import recall_at_k, mrr
from homework_3.data_loader import load_nq_dataset
import homework_3.config as config


top_k_test_values: List[int] = [1, 3, 10]


def run_tfidf(
    train_docs: List[str],
    test_queries: List[str],
    test_docs: List[str],
    top_k: List[int],
) -> Dict[str, float]:
    """
    1) Фитим TF-IDF на train_docs
    2) Векторизуем test_docs и test_queries
    3) Считаем cosine similarity query->all_docs
    4) Собираем ранжирование и метрики
    """
    vectorizer = TfidfVectorizer(
        ngram_range=config.TFIDF_NGRAM_RANGE,
        max_features=config.TFIDF_MAX_FEATURES,
    )
    vectorizer.fit(train_docs)

    doc_mat = vectorizer.transform(test_docs)
    q_mat = vectorizer.transform(test_queries)

    sim = cosine_similarity(q_mat, doc_mat)

    predictions = sim.argsort(axis=1)[:, ::-1].tolist()
    targets = list(range(len(test_docs)))

    results = {}

    for k in top_k:
        results[f"recall@{k}"] = recall_at_k(targets, predictions, k)

    results["mrr"] = mrr(targets, predictions)
    return results

def main():
    print("Загрузка и сплит датасета")
    train_q, train_d, test_q, test_d = load_nq_dataset(
        config.DATASET_NAME, config.TEST_SIZE, config.SEED
    )
    # Слишком люто память жрёт, поэтому срезаю часть
    train_d = train_d[:40000]
    test_d = test_d[:8000]
    train_q = train_q[:40000]
    test_q = test_q[:8000]
    print(f"  train: {len(train_d)} примеров, test: {len(test_d)} примеров\n")

    print("TF-IDF baseline")
    tfidf_res = run_tfidf(train_d, test_q, test_d, top_k_test_values)
    for k, v in tfidf_res.items():
        print(f"   {k}: {v:.4f}")
    print()

if __name__ == "__main__":
    main()

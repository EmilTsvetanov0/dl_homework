# data_loader.py
from datasets import load_dataset

def load_nq_dataset(dataset_name: str, test_size: float, seed: int):
    """
    Загружает датасет, сплитит в пропорции 1-test_size / test_size,
    возвращает четыре списка строк: train_queries, train_docs, test_queries, test_docs.
    Предполагаем, что в записи есть поля 'query' и 'answer'.
    """
    # обычно в этом датасете единственный сплит 'train'
    raw = load_dataset(dataset_name, split="train")
    splitted = raw.train_test_split(test_size=test_size, seed=seed)
    train_ds = splitted["train"]
    test_ds = splitted["test"]

    # Если названия полей отличаются, заменить здесь
    train_queries = train_ds["query"]
    train_docs    = train_ds["answer"]
    test_queries  = test_ds["query"]
    test_docs     = test_ds["answer"]

    return train_queries, train_docs, test_queries, test_docs

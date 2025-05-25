# HuggingFace‐датасет и сплит
DATASET_NAME = "sentence-transformers/natural-questions"
TEST_SIZE = 0.2
SEED = 42

# Параметры TF-IDF
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MAX_FEATURES = 10000

# Модель E5
E5_MODEL_NAME = "intfloat/multilingual-e5-base"

# При необходимости размер батча для E5-энкодинга
E5_BATCH_SIZE = 64
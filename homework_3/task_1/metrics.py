def recall_at_k(targets: list[int], predictions: list[list[int]], k: int) -> float:
    assert len(targets) == len(predictions)
    hit = 0
    for t, preds in zip(targets, predictions):
        if t in preds[:k]:
            hit += 1
    return hit / len(targets)


def mrr(targets: list[int], predictions: list[list[int]]) -> float:
    assert len(targets) == len(predictions)
    rr_total = 0.0
    for t, preds in zip(targets, predictions):
        try:
            rank = preds.index(t) + 1
            rr_total += 1.0 / rank
        except ValueError:
            pass
    return rr_total / len(targets)
import random
from typing import Any

import torch.nn.functional as F
import torch.utils.data
from accelerate.utils import set_seed
from datasets import load_dataset, Dataset
from torch import Tensor
from transformers import AutoTokenizer

from homework_3.task_4.config import RetrievalPipelineConfig


class RetrievalDataset(torch.utils.data.Dataset):
    def __init__(self, dataset: Dataset, cfg: RetrievalPipelineConfig, test_mode: bool):
        self._dataset = dataset
        self._tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
        self._config = cfg
        self._test_mode = test_mode

    def __len__(self):
        return len(self._dataset)

    def _tokenize(self, text: str) -> dict:
        encoding = self._tokenizer(text, max_length=self._config.max_length).encodings[0]
        return {
            'input_ids': torch.tensor(encoding.ids, dtype=torch.long),
            'attention_mask': torch.tensor(encoding.attention_mask, dtype=torch.long),
            'text': text
        }

    def __getitem__(self, index):
        positive_pair = self._dataset[index]
        if not self._test_mode:
            neg_idx = index
            while neg_idx == index:
                neg_idx = random.randint(0, len(self._dataset) - 1)
            negative_pair = self._dataset[neg_idx]
            negative_query = self._config.query_prefix + negative_pair['query']
        positive_query = self._config.query_prefix + positive_pair['query']
        anchor_document = self._config.document_prefix + positive_pair['answer']

        if self._test_mode:
            return {
                'positive': self._tokenize(positive_query),
                'anchor': self._tokenize(anchor_document)
            }
        else:
            return {
                'positive': self._tokenize(positive_query),
                'negative': self._tokenize(negative_query),
                'anchor': self._tokenize(anchor_document)
            }


class RetrievalCollator:
    def _stack_pad_tensors(self, items: list[Tensor]) -> Tensor:
        max_len = max(len(x) for x in items)
        items = [F.pad(x, (0, max_len - len(x)), mode='constant', value=0) for x in items]
        return torch.stack(items)

    def _collate_single(self, items: list[dict[str, Any]]):
        return {
            'input_ids': self._stack_pad_tensors([x['input_ids'] for x in items]),
            'attention_mask': self._stack_pad_tensors([x['attention_mask'] for x in items]),
            'text': [x['text'] for x in items],
        }

    def __call__(self, items):
        out_dict = {
            'positive': self._collate_single([x['positive'] for x in items]),
            'anchor': self._collate_single([x['anchor'] for x in items])
        }
        if 'negative' in items[0]:
            out_dict['negative'] = self._collate_single([x['negative'] for x in items])
        return out_dict


def load_data(cfg: RetrievalPipelineConfig, test_mode: bool):
    data = load_dataset(cfg.dataset)['train']
    data = data.train_test_split(test_size=0.025, seed=42, shuffle=True)
    if test_mode:
        return RetrievalDataset(data['test'], cfg, test_mode=test_mode)
    else:
        return RetrievalDataset(data['train'], cfg, test_mode=test_mode), RetrievalDataset(data['test'], cfg, test_mode=test_mode)
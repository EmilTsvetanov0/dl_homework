import torch
from torch import nn, Tensor

from dataset import _NUMERIC_DTYPES


class BaseBlock(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()
        self.bn = nn.BatchNorm1d(hidden_size)
        self.linear_1 = nn.Linear(hidden_size, hidden_size * 4)
        self.act = nn.LeakyReLU()
        self.linear_2 = nn.Linear(hidden_size * 4, hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.bn(x)
        x = self.linear_1(x)
        x = self.act(x)
        x = self.linear_2(x)
        return x


class LoanModel(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()

        self.emb_home = nn.Embedding(
            num_embeddings=4,
            embedding_dim=hidden_size
        )
        self.emb_intent = nn.Embedding(5, hidden_size)
        self.emb_grade = nn.Embedding(5, hidden_size)
        self.emb_default = nn.Embedding(2, hidden_size)

        self.numeric_linear = nn.Linear(7, hidden_size)

        self.blocks = nn.Sequential(
            BaseBlock(hidden_size),
            BaseBlock(hidden_size),
            BaseBlock(hidden_size),
            BaseBlock(hidden_size)
        )

        self.linear_out = nn.Linear(hidden_size, 1)

    def forward(self, cat_features: dict[str, Tensor], numeric_features: dict[str, Tensor]) -> Tensor:
        x_home = self.emb_home(cat_features['person_home_ownership'])
        x_intent = self.emb_intent(cat_features['loan_intent'])
        x_grade = self.emb_grade(cat_features['loan_grade'])
        x_default = self.emb_default(cat_features['cb_person_default_on_file'])

        stacked_numeric = torch.stack([
            numeric_features[col]
            for col in _NUMERIC_DTYPES
        ], dim=-1)
        x_numeric = self.numeric_linear(stacked_numeric)

        x_total = x_home + x_intent + x_grade + x_default + x_numeric

        x_total = self.block_1(x_total) + x_total
        x_total = self.block_2(x_total) + x_total
        x_total = self.block_3(x_total) + x_total
        x_total = self.block_4(x_total) + x_total

        result = self.linear_out(x_total)

        result = result.squeeze(-1)

        return result
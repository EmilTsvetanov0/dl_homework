import torch
from torch import nn, Tensor

from homework_1.dataset import _NUMERIC_DTYPES


class BaseBlock(nn.Module):
    def __init__(self, hidden_size: int, dropout_p: float):
        super().__init__()
        self.bn = nn.BatchNorm1d(hidden_size)
        self.linear_1 = nn.Linear(hidden_size, hidden_size * 4)
        self.act = nn.LeakyReLU()
        self.dropout = nn.Dropout(dropout_p)
        self.linear_2 = nn.Linear(hidden_size * 4, hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.bn(x)
        x = self.linear_1(x)
        x = self.act(x)
        x = self.dropout(x)
        x = self.linear_2(x)
        return x


class LoanModel(nn.Module):
    def __init__(self, hidden_size: int, dropout_p: float):
        super().__init__()

        self.emb_home = nn.Embedding(
            num_embeddings=4,
            embedding_dim=hidden_size
        )
        self.emb_intent = nn.Embedding(6, hidden_size)
        self.emb_grade = nn.Embedding(7, hidden_size)
        self.emb_default = nn.Embedding(2, hidden_size)

        self.numeric_bn = nn.BatchNorm1d(7)

        self.numeric_linear = nn.Linear(7, hidden_size)

        self.blocks = nn.ModuleList([
            BaseBlock(hidden_size * 5, dropout_p) for _ in range(3)
        ])

        self.linear_out = nn.Linear(hidden_size * 5, 1)

    def forward(self, cat_features: dict[str, Tensor], numeric_features: dict[str, Tensor]) -> Tensor:
        x_home = self.emb_home(cat_features['person_home_ownership'])
        x_intent = self.emb_intent(cat_features['loan_intent'])
        x_grade = self.emb_grade(cat_features['loan_grade'])
        x_default = self.emb_default(cat_features['cb_person_default_on_file'])

        stacked_numeric = torch.stack([
            numeric_features[col]
            for col in _NUMERIC_DTYPES
        ], dim=-1)
        x_numeric = self.numeric_bn(stacked_numeric)
        x_numeric = self.numeric_linear(x_numeric)

        x_total = torch.cat([x_home, x_intent, x_grade, x_default, x_numeric], dim=-1)

        for block in self.blocks:
            x_total = block(x_total) + x_total

        result = self.linear_out(x_total)

        result = result.squeeze(-1)

        return result
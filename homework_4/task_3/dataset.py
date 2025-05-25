from pathlib import Path

import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch import Tensor
from torch.utils.data import Dataset

_HOME_MAP = {
    'RENT': 0,
    'MORTGAGE': 1,
    'OWN': 2,
    'OTHER': 3
}

_INTENT_MAP = {
    'EDUCATION': 0,
    'MEDICAL': 1,
    'PERSONAL': 2,
    'VENTURE': 3,
    'DEBTCONSOLIDATION': 4,
    'HOMEIMPROVEMENT': 5
}

_GRADE_MAP = {
    'A': 0,
    'B': 1,
    'C': 2,
    'D': 3,
    'E': 4,
    'F': 5,
    'G': 6,
}

_CB_PERSON_DEFAULT_MAP = {
    'N': 0,
    'Y': 1
}

_NUMERIC_DTYPES = {
    "person_age": torch.long,
    'person_income': torch.long,
    "loan_amnt": torch.long,
    "cb_person_cred_hist_length": torch.long,

    "person_emp_length": torch.float32,
    "loan_int_rate": torch.float32,
    "loan_percent_income": torch.float32
}


class LoanDataset(Dataset):
    def __init__(self, data: pd.DataFrame):
        self._data = data

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item: int) -> dict[str, dict[str | Tensor] | Tensor]:
        item = self._data.iloc[item]
        return {
            'target': torch.scalar_tensor(item['loan_status'], dtype=torch.float32),
            'cat_features': {
                'person_home_ownership': torch.scalar_tensor(_HOME_MAP[item['person_home_ownership']], dtype=torch.long),
                'loan_intent': torch.scalar_tensor(_INTENT_MAP[item['loan_intent']], dtype=torch.long),
                'loan_grade': torch.scalar_tensor(_GRADE_MAP[item['loan_grade']], dtype=torch.long),
                'cb_person_default_on_file': torch.scalar_tensor(_CB_PERSON_DEFAULT_MAP[item['cb_person_default_on_file']], dtype=torch.long)
            },
            'numeric_features': {
                col: torch.scalar_tensor(
                    item[col],
                    dtype=_NUMERIC_DTYPES[col]
                )
                for col in _NUMERIC_DTYPES
            }
        }


class LoanCollator:
    def __call__(self, items: list[dict[str, dict[str | Tensor] | Tensor]]) -> dict[str, dict[str | Tensor] | Tensor]:
        return {
            'target': torch.stack([x['target'] for x in items]),
            'cat_features': {
                'person_home_ownership': torch.stack([x['cat_features']['person_home_ownership'] for x in items]),
                'loan_intent': torch.stack([x['cat_features']['loan_intent'] for x in items]),
                'loan_grade': torch.stack([x['cat_features']['loan_grade'] for x in items]),
                'cb_person_default_on_file': torch.stack([x['cat_features']['cb_person_default_on_file'] for x in items])
            },
            'numeric_features': {
                col: torch.stack([x['numeric_features'][col] for x in items])
                for col in _NUMERIC_DTYPES
            }
        }


def load_loan_data(file: Path) -> tuple[LoanDataset, LoanDataset]:
    df = pd.read_csv(file)
    df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['loan_status'])
    return LoanDataset(df_train), LoanDataset(df_test)
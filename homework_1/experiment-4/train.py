from pathlib import Path

import torch
from aim import Run
from torch.nn import BCEWithLogitsLoss
from torch.optim import SGD
from torch.utils.data import Dataset, DataLoader
from torchmetrics import MeanMetric, AUROC
from tqdm import tqdm

from homework_1.dataset import LoanCollator, load_loan_data, _NUMERIC_DTYPES
from model import LoanModel

def _map_to_device(batch: dict, dev: torch.device) -> dict:
    batch['target'] = batch['target'].to(dev)
    batch['cat_features']['person_home_ownership'] = batch['cat_features']['person_home_ownership'].to(dev)
    batch['cat_features']['loan_intent'] = batch['cat_features']['loan_intent'].to(dev)
    batch['cat_features']['loan_grade'] = batch['cat_features']['loan_grade'].to(dev)
    batch['cat_features']['cb_person_default_on_file'] = batch['cat_features']['cb_person_default_on_file'].to(dev)

    for col in _NUMERIC_DTYPES:
        batch['numeric_features'][col] = batch['numeric_features'][col].to(dev)



def train(train_dataset: Dataset, eval_dataset: Dataset):
    dev = torch.device('cuda:0')
    n_epochs = 15
    lr = 0.01
    base_hidden_size = 128
    dropout_p = 0.2
    batch_size = 32
    seed = 42
    weight_decay = 0.01

    torch.random.manual_seed(seed)


    loss_bce = BCEWithLogitsLoss()

    collator = LoanCollator()
    model = LoanModel(hidden_size=base_hidden_size, dropout_p=dropout_p).to(dev)
    optimizer = SGD(model.parameters(), lr=lr, weight_decay=weight_decay)

    run = Run(experiment='123')
    run["hparams"] = {
        "learning_rate": lr,
        "base_hidden_size": base_hidden_size,
        "batch_size": batch_size,
        'weight_decay': weight_decay
    }

    train_dl = DataLoader(train_dataset, batch_size=batch_size, num_workers=16, collate_fn=collator, pin_memory=True)
    eval_dl = DataLoader(eval_dataset, batch_size=batch_size, num_workers=16, collate_fn=collator, pin_memory=True)

    for i_epoch in tqdm(range(n_epochs)):
        train_loss = MeanMetric().to(dev)
        train_rocauc = AUROC(task='binary').to(dev)
        for i, batch in enumerate(train_dl):
            _map_to_device(batch, dev)

            result = model(cat_features=batch['cat_features'], numeric_features=batch['numeric_features'])
            loss_value = loss_bce(result, batch['target'])
            loss_value.backward()
            optimizer.step()
            optimizer.zero_grad()

            train_loss.update(loss_value)
            train_rocauc.update(torch.sigmoid(result), batch['target'])

        train_loss = train_loss.compute().item()
        train_rocauc = train_rocauc.compute().item()
        run.track(train_loss, name='loss/train', step=i_epoch)
        run.track(train_rocauc, name='roc-auc/train', step=i_epoch)

        eval_loss = MeanMetric().to(dev)
        eval_rocauc = AUROC(task='binary').to(dev)

        model.eval()
        with torch.no_grad():
            for i_eval, batch_eval in enumerate(eval_dl):
                _map_to_device(batch_eval, dev)

                result_eval = model(cat_features=batch_eval['cat_features'], numeric_features=batch_eval['numeric_features'])
                eval_loss_value = loss_bce(result_eval, batch_eval['target'])

                eval_loss.update(eval_loss_value)
                eval_rocauc.update(torch.sigmoid(result_eval), batch_eval['target'])
        model.train()

        eval_loss = eval_loss.compute().item()
        eval_rocauc = eval_rocauc.compute().item()
        run.track(eval_loss, name='loss/eval', step=i_epoch)
        run.track(eval_rocauc, name='roc-auc/eval', step=i_epoch)



if __name__ == '__main__':
    train_ds, test_ds = load_loan_data(Path('/home/shovel/PycharmProjects/dl_homework/homework_1/train_loan.csv'))
    train(train_ds, test_ds)
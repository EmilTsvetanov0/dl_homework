import torch
import numpy as np
from torch.optim.optimizer import Optimizer

class Lion(Optimizer):
    def __init__(self,
                 params,
                 lr: float = 1e-3,
                 beta1: float = 0.9,
                 beta2: float = 0.99,
                 weight_decay: float = 0.0):
        defaults = dict(lr=lr, beta1=beta1, beta2=beta2, weight_decay=weight_decay)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        for group in self.param_groups:
            lr = group['lr']
            b1 = group['beta1']
            b2 = group['beta2']
            wd = group['weight_decay']
            for p in group['params']:
                if p.grad is None:
                    continue
                grad = p.grad

                state = self.state[p]
                if 'momentum' not in state:
                    state['momentum'] = torch.zeros_like(p)

                m = state['momentum']

                update = grad.mul(1 - b1).add(m, alpha=b1)
                update_sign = update.sign()

                m_new = grad.mul(1 - b2).add(m, alpha=b2)
                state['momentum'] = m_new

                if wd != 0:
                    update_sign = update_sign.add(p, alpha=wd)

                p.add_(update_sign, alpha=-lr)
        return None

# if __name__ == '__main__':
#     # Обучим маленькую линейную модель на случайных данных
#     torch.manual_seed(0)
#     model = torch.nn.Linear(10, 1)
#     opt = Lion(model.parameters(), lr=1e-2, weight_decay=1e-4)
#     for i in range(100):
#         x = torch.randn(16, 10)
#         y = torch.randn(16, 1)
#         y_pred = model(x)
#         loss = torch.nn.functional.mse_loss(y_pred, y)
#         opt.zero_grad(); loss.backward(); opt.step()
#     print("Lion smoke-test finished, final loss:", loss.item())

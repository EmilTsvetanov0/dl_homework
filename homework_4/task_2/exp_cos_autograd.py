import torch

class ExpCos(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x: torch.Tensor, y: torch.Tensor):
        # сохраняем для backward exp(x) и sin(y), чтобы не пересчитывать
        exp_x = x.exp()
        sin_y = y.sin()
        ctx.save_for_backward(exp_x, sin_y)
        return exp_x + y.cos()

    @staticmethod
    def backward(ctx, grad_output):
        exp_x, sin_y = ctx.saved_tensors
        # d/dx e^x = e^x, d/dy cos(y) = -sin(y)
        dx = grad_output * exp_x
        dy = grad_output * (-sin_y)
        return dx, dy

def exp_cos(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return ExpCos.apply(x, y)

def _test():
    torch.manual_seed(42)
    x = torch.randn(5, requires_grad=True)
    y = torch.randn(5, requires_grad=True)

    # эталон
    z_ref = x.exp() + y.cos()
    l_ref = z_ref.sum()
    l_ref.backward()
    gx_ref, gy_ref = x.grad.clone(), y.grad.clone()

    # мой
    x.grad.zero_(); y.grad.zero_()
    z = exp_cos(x, y)
    l = z.sum()
    l.backward()
    gx, gy = x.grad, y.grad

    assert torch.allclose(gx, gx_ref, atol=1e-6)
    assert torch.allclose(gy, gy_ref, atol=1e-6)
    print("ExpCos autograd OK")

if __name__ == '__main__':
    _test()

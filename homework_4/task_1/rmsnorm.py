import torch
from torch import nn

class RMSNorm(nn.Module):
    def __init__(self,
                 normalized_shape: int or tuple,
                 eps: float = 1e-8,
                 elementwise_affine: bool = True):
        super().__init__()
        if isinstance(normalized_shape, int):
            normalized_shape = (normalized_shape,)
        self.normalized_shape = tuple(normalized_shape)
        self.eps = eps
        if elementwise_affine:
            self.weight = nn.Parameter(torch.ones(self.normalized_shape))
        else:
            self.register_parameter('weight', None)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        dims = tuple(range(-len(self.normalized_shape), 0))
        rms = x.pow(2).mean(dim=dims, keepdim=True).add(self.eps).sqrt()

        x_normed = x / rms
        if self.weight is not None:
            x_normed = x_normed * self.weight

        return x_normed

if __name__ == '__main__':
    torch.manual_seed(0)
    B, T, C = 2, 4, 8
    x = torch.randn(B, T, C, dtype=torch.float32)
    my = RMSNorm(C, eps=1e-5)
    ref = nn.RMSNorm(C, eps=1e-5)

    with torch.no_grad():
        ref.weight.copy_(my.weight)
    y1 = my(x)
    y2 = ref(x)
    assert torch.allclose(y1, y2, atol=1e-6), "RMSNorm mismatch"
    print("RMSNorm OK")

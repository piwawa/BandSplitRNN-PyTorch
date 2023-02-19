import torch
import torch.nn as nn
from typing import List, Tuple

from .utils import freq2bands


class GLU(nn.Module):
    def __init__(self, input_dim: int):
        super(GLU, self).__init__()
        self.input_dim = input_dim
        self.linear = nn.Linear(input_dim, input_dim * 2)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor):
        x = self.linear(x)
        x = x[..., :self.input_dim] * self.sigmoid(x[..., self.input_dim:])
        return x


class MLP(nn.Module):
    def __init__(
            self,
            input_dim: int,
            hidden_dim: int,
            output_dim: int,
            activation_type: str = 'tanh',
    ):
        super(MLP, self).__init__()

        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            self.select_activation(activation_type)(),
            nn.Linear(hidden_dim, output_dim),
            GLU(output_dim)
        )

    @staticmethod
    def select_activation(activation_type: str) -> nn.modules.activation:
        if activation_type == 'tanh':
            return nn.Tanh
        elif activation_type == 'relu':
            return nn.ReLU
        elif activation_type == 'gelu':
            return nn.GELU
        else:
            raise ValueError("wrong activation function was selected")

    def forward(self, x: torch.Tensor):
        x = self.mlp(x)
        return x


class MaskEstimationModule(nn.Module):
    """

    """

    def __init__(
            self,
            sr: int,
            n_fft: int,
            bandsplits: List[Tuple[int, int]],
            t_timesteps: int = 517,
            fc_dim: int = 128,
            mlp_dim: int = 512
    ):
        super(MaskEstimationModule, self).__init__()
        self.bandwidths = [(e - s) for s, e in freq2bands(bandsplits, sr, n_fft)]
        self.layernorms = nn.ModuleList([
            nn.LayerNorm([t_timesteps, fc_dim])
            for _ in range(len(self.bandwidths))
        ])
        self.mlp = nn.ModuleList([
            MLP(fc_dim, mlp_dim, bw, activation_type='tanh')
            for bw in self.bandwidths
        ])

    def forward(self, x: torch.Tensor):
        """
        Input: [batch_size, k_subbands, time, fc_shape]
        Output: [batch_size, freq, time]
        """
        outs = []
        for i in range(x.shape[1]):
            out = self.layernorms[i](x[:, i])
            out = self.mlp[i](out)
            outs.append(out)
        outs = torch.cat(outs, dim=-1)
        outs = outs.transpose(-1, -2)
        return outs.unsqueeze(1)


if __name__ == '__main__':
    batch_size, k_subbands, t_timesteps, input_dim = 8, 41, 517, 128
    in_features = torch.rand(batch_size, k_subbands, t_timesteps, input_dim)

    cfg = {
        "sr": 44100,
        "n_fft": 2048,
        "bandsplits": [
            (1000, 100),
            (4000, 250),
            (8000, 500),
            (16000, 1000),
            (20000, 2000),
        ],
        "t_timesteps": 517,
        "fc_dim": 128,
        "mlp_dim": 512,
    }
    model = MaskEstimationModule(
        **cfg
    )
    _ = model.eval()

    with torch.no_grad():
        out_features = model(in_features)

    print(model)
    print(f"Total number of parameters: {sum([p.numel() for p in model.parameters()])}")
    print(f"In: {in_features.shape}\nOut: {out_features.shape}")
#!/usr/bin/env python3
"""
mogernn_adapter.py — MoGERNN (reference commit 86b153fb4bf9358e32079930ccaea1cbcffa66f8) on the E11 perimeter, as
specified by `rafforzamento/ADAPTER_SPEC_E14.md` (binding). Imported by `e14.py`; frozen with it.
=======================================================================================================================
Two operating modes of one module tree, so that the equivalence with the original can be asserted on the very modules E14
trains:

  mode "original"  — the original `Model` of `model/MoGERNN.py`: single channel, unknown nodes = nodes whose batch sum is 0,
                     replacement where the value is 0 (`miss_ix = (x == 0)`), teacher forcing drawn per decoder step with the
                     ratio 1 − epoch/40 while training, random walks recomputed at every forward. Parameter names equal the
                     original's, so `load_state_dict` works in both directions; the preflight asserts forward equality.
  mode "masked"    — the adapter of E14 (ADAPTER_SPEC §1–§3): the experts receive the factor channel only; unknown nodes =
                     nodes with `node_in = 0`; replacement index = 1 − `m_in` (missing reading or non-input node; a valid
                     standardised value exactly 0 is never replaced); exogenous channels (`m_in`, five calendar channels and,
                     in S1, two standardised coordinates) concatenated to the completed factor as inputs of the recurrent
                     cells of encoder and decoder; `fc: 64 → 1`; decoder first input = completed last step; teacher forcing
                     absent by construction; random walks passed in (cached once per city by the caller).

Everything marked [original] below is a transcription of the original code (same operations, same quirks, same names);
everything marked [adaptation] is a declared departure of ADAPTER_SPEC_E14.md. `einops.rearrange` is replaced by the
equivalent `permute`/`reshape`; `torch.eye(...)` is created on the tensor's device (the original creates it on the CPU).

Also here, because they belong to the method's own machinery: `random_walk_matrix` [original, scipy on the CPU],
`method_graph` (ADAPTER_SPEC §6: Gaussian kernel on road-network distance within a declared road radius of 2 km, threshold 0.1, zero diagonal), the boolean
dependency propagation of C0.5(a) (`dependency_rows`, an upper bound: an empty row excludes a dependence, a non-empty row does
not demonstrate one), the hop distance on A ∪ Aᵀ and the reference linear mass.
"""
import math
from collections import deque

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn.functional as F
from torch import nn

ORIGINAL_COMMIT = "86b153fb4bf9358e32079930ccaea1cbcffa66f8"
EXPERT_ORDER = ("mean", "weight", "max", "min", "diffusion")       # args.py order: mean_expert, weight_expert, max_expert, min_expert, diffusion_expert


# ---------------------------------------------------------------- random walk [original] ------------------

def random_walk_matrix(adj):
    """layers/gnn.py::calculate_random_walk_matrix, same operations: scipy on the CPU, d = 0 → 1, D⁻¹A, back to the device
    in the adjacency's dtype (float32 in the campaign, as the original's `.float()`; float64 in the sensitivity diagnostic)."""
    device = adj.device
    a = adj.detach().cpu().numpy()
    a = sp.coo_matrix(a)
    d = np.array(a.sum(1))
    d = np.where(d == 0, 1, d)
    d_inv = np.power(d, -1).flatten()
    d_inv[np.isinf(d_inv)] = 0.
    d_mat_inv = sp.diags(d_inv)
    rw = d_mat_inv.dot(a).tocoo()
    return torch.from_numpy(rw.toarray()).to(adj.dtype).to(device)       # float32 in → float32 out, as the original's .float()


# ---------------------------------------------------------------- diffusion convolution [original] --------

class DiffConv(nn.Module):
    """layers/DCRNNCell.py::DiffConv: Chebyshev-style diffusion over two supports A_q, A_h of order k → 2k + 1 matrices
    (I, A_q^1..k, A_h^1..k). `torch.where(adj > 0, 1., 0.)` of the experts is written with ones_like/zeros_like (same values,
    dtype-safe for the float64 diagnostic)."""

    def __init__(self, in_channels, out_channels, k_hop):
        super().__init__()
        self.orders = k_hop
        self.num_matrices = 2 * self.orders + 1
        self.Theta1 = nn.Parameter(torch.FloatTensor(in_channels * self.num_matrices, out_channels))
        self.bias = nn.Parameter(torch.FloatTensor(out_channels))
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.Theta1.shape[1])
        self.Theta1.data.uniform_(-stdv, stdv)
        stdv1 = 1. / math.sqrt(self.bias.shape[0])
        self.bias.data.uniform_(-stdv1, stdv1)

    @staticmethod
    def _concat(x, x_):
        return torch.cat([x, x_.unsqueeze(0)], dim=0)

    def forward(self, X, A_q, A_h):
        """X: (batch, nodes, channels) → (batch, nodes, out_channels)."""
        batch_size, num_node, input_size = X.shape[0], X.shape[1], X.size(2)
        x0 = X.permute(1, 2, 0)
        x0 = torch.reshape(x0, shape=[num_node, input_size * batch_size])
        x = torch.unsqueeze(x0, 0)
        for support in (A_q, A_h):
            x1 = torch.mm(support, x0)
            x = self._concat(x, x1)
            for _ in range(2, self.orders + 1):
                x2 = 2 * torch.mm(support, x1) - x0
                x = self._concat(x, x2)
                x1, x0 = x2, x1
        x = torch.reshape(x, shape=[self.num_matrices, num_node, input_size, batch_size])
        x = x.permute(3, 1, 2, 0)
        x = torch.reshape(x, shape=[batch_size, num_node, input_size * self.num_matrices])
        x = torch.matmul(x, self.Theta1)
        x = x + self.bias
        return x


class DCRNNCell(nn.Module):
    """layers/DCRNNCell.py::DCRNNCell on layers/GRUCell.py::GraphGRUCellBase: three DiffConv gates on [x ; h]; the gate the
    original names `forget_gate` is the reset gate r, which multiplies h before the candidate (so two convolutions compose
    inside one cell: the dependency propagation of C0.5(a) relies on exactly this)."""

    def __init__(self, input_size, hidden_size, k=2):
        super().__init__()
        self.hidden_size = hidden_size
        self.forget_gate = DiffConv(input_size + hidden_size, hidden_size, k)
        self.update_gate = DiffConv(input_size + hidden_size, hidden_size, k)
        self.candidate_gate = DiffConv(input_size + hidden_size, hidden_size, k)

    def forward(self, x, h, A_q, A_h):
        x_gates = torch.cat([x, h], dim=-1)
        r = torch.sigmoid(self.forget_gate(x_gates, A_q, A_h))
        u = torch.sigmoid(self.update_gate(x_gates, A_q, A_h))
        x_c = torch.cat([x, r * h], dim=-1)
        c = torch.tanh(self.candidate_gate(x_c, A_q, A_h))
        return u * h + (1. - u) * c


# ---------------------------------------------------------------- experts [original] ----------------------

class MeanAggregator(nn.Module):
    """layers/agg.py: row aggregation on the unweighted degree; the unknown nodes' columns are zeroed first."""

    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim, bias=False)
        self.fc2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU())

    def forward(self, adj, x, batch_unknown_nodes, *args):
        adj = adj.clone()
        x = self.fc1(x)
        adj[:, batch_unknown_nodes] = 0
        unweighted_adj = torch.where(adj > 0, torch.ones_like(adj), torch.zeros_like(adj))
        degree = torch.sum(unweighted_adj, dim=1, keepdim=True)
        degree[degree == 0] = 1
        norm_adj = adj / degree
        return self.fc2(torch.matmul(norm_adj, x))


class WMeanAggregator(nn.Module):
    """layers/agg.py: row aggregation on the weighted degree."""

    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim, bias=False)
        self.fc2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU())

    def forward(self, adj, x, batch_unknown_nodes, *args):
        adj = adj.clone()
        x = self.fc1(x)
        adj[:, batch_unknown_nodes] = 0
        degree = torch.sum(adj, dim=1, keepdim=True)
        degree[degree == 0] = 1
        norm_adj = adj / degree
        return self.fc2(torch.matmul(norm_adj, x))


class MaxPoolingAggregator(nn.Module):
    """layers/agg.py: node l receives max_k x(k)·1[adj(k, l) > 0] — the COLUMN of the adjacency; non-neighbours contribute
    0 to the maximum, and an unknown node (zeroed column) receives exactly 0. Kept as in the code (audit §5)."""

    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim, bias=False)
        self.fc2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU())

    def forward(self, adj, x, batch_unknown_nodes, *args):
        adj = adj.clone()
        x = self.fc1(x)
        adj[:, batch_unknown_nodes] = 0
        adj = torch.where(adj > 0, torch.ones_like(adj), torch.zeros_like(adj))
        x = x.permute(0, 2, 1)
        neighbor_features = torch.einsum('ijk,kl->ijkl', x, adj).permute(0, 1, 3, 2)
        pooled = torch.max(neighbor_features, dim=-1).values
        return self.fc2(pooled.permute(0, 2, 1))


class MinPoolingAggregator(nn.Module):
    """layers/agg.py: as MaxPooling with the minimum (non-neighbours contribute 0 to the minimum as well)."""

    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim, bias=False)
        self.fc2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU())

    def forward(self, adj, x, batch_unknown_nodes, *args):
        adj = adj.clone()
        x = self.fc1(x)
        adj[:, batch_unknown_nodes] = 0
        adj = torch.where(adj > 0, torch.ones_like(adj), torch.zeros_like(adj))
        x = x.permute(0, 2, 1)
        neighbor_features = torch.einsum('ijk,kl->ijkl', x, adj).permute(0, 1, 3, 2)
        pooled = torch.min(neighbor_features, dim=-1).values
        return self.fc2(pooled.permute(0, 2, 1))


class D_GCN(nn.Module):
    """layers/gnn.py::D_GCN with activation 'identity' (the only use in the configuration): DiffConv with an in-place bias."""

    def __init__(self, in_channels, out_channels, k_hop):
        super().__init__()
        self.orders = k_hop
        self.num_matrices = 2 * self.orders + 1
        self.Theta1 = nn.Parameter(torch.FloatTensor(in_channels * self.num_matrices, out_channels))
        self.bias = nn.Parameter(torch.FloatTensor(out_channels))
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.Theta1.shape[1])
        self.Theta1.data.uniform_(-stdv, stdv)
        stdv1 = 1. / math.sqrt(self.bias.shape[0])
        self.bias.data.uniform_(-stdv1, stdv1)

    def forward(self, X, A_q, A_h):
        batch_size, num_node, input_size = X.shape[0], X.shape[1], X.size(2)
        x0 = torch.reshape(X.permute(1, 2, 0), shape=[num_node, input_size * batch_size])
        x = torch.unsqueeze(x0, 0)
        for support in (A_q, A_h):
            x1 = torch.mm(support, x0)
            x = torch.cat([x, x1.unsqueeze(0)], dim=0)
            for _ in range(2, self.orders + 1):
                x2 = 2 * torch.mm(support, x1) - x0
                x = torch.cat([x, x2.unsqueeze(0)], dim=0)
                x1, x0 = x2, x1
        x = torch.reshape(x, shape=[self.num_matrices, num_node, input_size, batch_size]).permute(3, 1, 2, 0)
        x = torch.reshape(x, shape=[batch_size, num_node, input_size * self.num_matrices])
        x = torch.matmul(x, self.Theta1)
        x = x + self.bias
        return x


class DiffusionAggregator(nn.Module):
    """layers/agg.py: random walks of the adjacency with the unknown columns zeroed (rows: A_q; columns: A_h), recomputed
    at every call because the unknown set changes with the batch — the original behaviour, kept."""

    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim, bias=False)
        self.conv = D_GCN(hidden_dim, hidden_dim, 1)
        self.fc2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU())

    def forward(self, adj, x, batch_unknown_nodes, *args):
        if len(args) == 0:
            adj = adj.clone()
            adj_h = adj.T.clone()
            adj[:, batch_unknown_nodes] = 0
            adj_h[:, batch_unknown_nodes] = 0
            A_q = random_walk_matrix(adj)
            A_h = random_walk_matrix(adj_h)
        else:
            A_q, A_h = args
        x = self.fc1(x)
        x = self.conv(x, A_q, A_h)
        return self.fc2(x)


class Expert(nn.Module):
    """model/MoGERNN.py::Expert (module name `completion`, kept for the parameter names)."""

    def __init__(self, completion):
        super().__init__()
        self.completion = completion

    def forward(self, adj, x_enc, batch_unknown_nodes):
        return self.completion(adj, x_enc, batch_unknown_nodes)


class SparseGatingNetwork(nn.Module):
    """model/MoGERNN.py::SparseGatingNetwork: Linear(T → d_model), ReLU, Linear(d_model → E), top-k, softmax over the k kept
    logits scattered into zeros."""

    def __init__(self, input_len, d_model, num_experts, num_used_experts):
        super().__init__()
        self.fc1 = nn.Linear(input_len, d_model)
        self.fc2 = nn.Linear(d_model, num_experts)
        self.k = num_used_experts

    def forward(self, x):
        x = F.relu(self.fc1(x))
        logits = self.fc2(x)
        top_logits, topk_indices = torch.topk(logits, self.k, dim=-1)
        zeros = torch.zeros_like(logits)
        return zeros.scatter(2, topk_indices, F.softmax(top_logits, dim=-1))


class DataPreparation(nn.Module):
    """model/MoGERNN.py::DataPreparation with the completion driver factored out: `combine` is the experts' weighted
    completion [original]; the caller decides the unknown set and the replacement index (mode original / mode masked)."""

    def __init__(self, input_len, d_model, num_used_experts=3, experts=EXPERT_ORDER):
        super().__init__()
        cls = {"mean": MeanAggregator, "weight": WMeanAggregator, "max": MaxPoolingAggregator, "min": MinPoolingAggregator,
               "diffusion": DiffusionAggregator}
        self.expert_names = tuple(experts)
        self.experts = nn.ModuleList([Expert(cls[n](input_len, input_len)) for n in self.expert_names])
        self.gating = SparseGatingNetwork(input_len, d_model, len(self.expert_names), num_used_experts)

    @staticmethod
    def no_self_loops(adj):
        adj_noselfloop = adj.clone()
        adj_noselfloop[torch.eye(adj.shape[0], dtype=torch.bool, device=adj.device)] = 0
        return adj_noselfloop

    def combine(self, adj, x_bnt, batch_unknown_nodes):
        """[original] gate weights from each node's own series; experts on the adjacency without self-loops and with the
        unknown columns zeroed; weighted sum over the experts. x_bnt: (B, N, T) → (B, N, T)."""
        gate_weights = self.gating(x_bnt)
        adj_noselfloop = self.no_self_loops(adj)
        expert_outputs = [expert(adj_noselfloop, x_bnt, batch_unknown_nodes) for expert in self.experts]
        stack = torch.stack(expert_outputs, dim=2)
        return torch.sum(gate_weights.unsqueeze(-1) * stack, dim=2)

    def complete(self, adj, x_bnt, batch_unknown_nodes, miss_ix):
        """x · (1 − miss) + combined · miss, with the replacement index given by the caller (float 0/1, (B, N, T))."""
        combined = self.combine(adj, x_bnt, batch_unknown_nodes)
        return x_bnt * (1 - miss_ix) + combined * miss_ix, combined


class Encoder(nn.Module):
    """model/MoGERNN.py::Encoder: `num_layers` DCRNN cells; the first takes `input_size` channels."""

    def __init__(self, input_size, hidden_size, num_layers, k=2):
        super().__init__()
        self.hidden_size, self.num_layers = hidden_size, num_layers
        self.rnn_cells = nn.ModuleList([DCRNNCell(input_size if i == 0 else hidden_size, hidden_size, k) for i in range(num_layers)])

    def forward(self, x, A_q, A_h, h0=None):
        batch_size, seq_len, num_nodes, _ = x.size()
        hidden_state = h0 if h0 is not None else torch.zeros(self.num_layers, batch_size, num_nodes, self.hidden_size, device=x.device, dtype=x.dtype)
        for t in range(seq_len):
            hs = []
            inp = x[:, t, :, :]
            for layer in range(self.num_layers):
                next_hidden = self.rnn_cells[layer](inp, hidden_state[layer], A_q, A_h)
                inp = next_hidden
                hs.append(next_hidden)
            hidden_state = torch.stack(hs, dim=0)
        return hidden_state


class Decoder(nn.Module):
    """model/MoGERNN.py::Decoder: `num_layers` DCRNN cells (Seq2Seq passes the encoder's number: two), `fc: hidden → out`.
    [original] `fc: hidden → input_size` (= 1 in the configuration); [adaptation] the cells take 1 + exogenous channels while
    `fc` still outputs the single factor channel."""

    def __init__(self, input_size, hidden_size, out_seq_len, num_layers=1, k=2, out_size=1):
        super().__init__()
        self.input_size, self.hidden_size, self.num_layers, self.out_seq_len = input_size, hidden_size, num_layers, out_seq_len
        self.rnn_cells = nn.ModuleList([DCRNNCell(input_size if i == 0 else hidden_size, hidden_size, k) for i in range(num_layers)])
        self.fc = nn.Linear(hidden_size, out_size)

    def _step(self, input_at_t, h, A_q, A_h):
        hs = []
        for layer in range(self.num_layers):
            next_h = self.rnn_cells[layer](input_at_t, h[layer], A_q, A_h)
            input_at_t = next_h
            hs.append(next_h)
        return torch.stack(hs, dim=0), self.fc(next_h)

    def forward_original(self, initial_input, h, A_q, A_h, teacher_input, teacher_forcing_ratio=0.5):
        """[original] one draw of torch.rand(1) per step while training; the drawn step feeds the target, else the output."""
        input_at_t = initial_input
        outputs = [None for _ in range(self.out_seq_len)]
        for t in range(self.out_seq_len):
            h, output = self._step(input_at_t, h, A_q, A_h)
            outputs[t] = output
            use_teacher_forcing = True if (torch.rand(1).item() < teacher_forcing_ratio and self.training) else False
            input_at_t = teacher_input[:, t] if use_teacher_forcing else outputs[t]
        return torch.stack(outputs, dim=1)

    def forward_masked(self, initial_factor, h, A_q, A_h, exogenous):
        """[adaptation] input at step t = [previous factor ; exogenous(t)], previous factor = the completed last input step at
        t = 0 and the previous output afterwards; no teacher forcing. `exogenous(t)`: (B, N, E)."""
        prev = initial_factor
        outputs = [None for _ in range(self.out_seq_len)]
        for t in range(self.out_seq_len):
            h, output = self._step(torch.cat([prev, exogenous(t)], dim=-1), h, A_q, A_h)
            outputs[t] = output
            prev = output
        return torch.stack(outputs, dim=1)


class Seq2Seq(nn.Module):
    """model/MoGERNN.py::Seq2Seq: the same `num_layers` for encoder and decoder."""

    def __init__(self, input_size, hidden_size, num_layers, out_seq_len, k=2, out_size=1):
        super().__init__()
        self.encoder = Encoder(input_size, hidden_size, num_layers, k)
        self.decoder = Decoder(input_size, hidden_size, out_seq_len, num_layers, k, out_size)


class MoGERNN(nn.Module):
    """The model. `mode='original'` reproduces `model/MoGERNN.py::Model` (preflight equivalence); `mode='masked'` is the E14
    adapter. Module names `data_pre` and `seq2seq` as the original."""

    def __init__(self, input_len=12, pred_len=8, d_model=64, e_layers=2, k_hop=1, num_used_experts=3, exo_channels=0, mode="masked",
                 experts=EXPERT_ORDER):
        super().__init__()
        if mode not in ("original", "masked"):
            raise ValueError(mode)
        if mode == "original" and exo_channels != 0:
            raise ValueError("the original configuration has no exogenous channel")
        self.mode, self.input_len, self.pred_len, self.exo_channels = mode, input_len, pred_len, exo_channels
        self.data_pre = DataPreparation(input_len, d_model, num_used_experts, experts)
        self.seq2seq = Seq2Seq(1 + exo_channels, d_model, e_layers, pred_len, k_hop, out_size=1)

    def parameter_count(self):
        return int(sum(p.numel() for p in self.parameters()))

    # ---- [original] -----------------------------------------------------------------------------------------
    def forward_original(self, adj, x_enc, x_dec=None, epoch=0):
        """model/MoGERNN.py::Model.forward with enc_in = 1: x_enc (B, T, N, 1), x_dec (B, H, N, 1) or None (evaluation),
        teacher forcing ratio 1 − epoch/40; random walks recomputed here."""
        if self.mode != "original":
            raise RuntimeError("forward_original is the original configuration only")
        A_q = random_walk_matrix(adj)
        A_h = random_walk_matrix(adj.T)
        x = x_enc.squeeze(-1)
        batch_unknown_nodes = torch.where(torch.sum(x, dim=(0, 1)) == 0)[0].cpu().tolist()
        x_bnt = x.permute(0, 2, 1)
        miss_ix = (x_bnt == 0).to(x_bnt.dtype)
        xc, _ = self.data_pre.complete(adj, x_bnt, batch_unknown_nodes, miss_ix)
        x_c = xc.permute(0, 2, 1).unsqueeze(-1)
        teacher_forcing_ratio = 1 - (epoch / 40)
        h = self.seq2seq.encoder(x_c, A_q, A_h)
        return self.seq2seq.decoder.forward_original(x_c[:, -1], h, A_q, A_h, x_dec, teacher_forcing_ratio)

    # ---- [adaptation] ---------------------------------------------------------------------------------------
    def complete_masked(self, adj, r_in, m_in, node_in):
        """Mask-driven completion: unknown = nodes with node_in = 0; replacement index = 1 − m_in. r_in, m_in: (B, T, N, 1);
        node_in: (N,). Returns the completed factor r_c (B, T, N, 1) and the experts' combination (B, T, N, 1)."""
        x_bnt = r_in[..., 0].permute(0, 2, 1)
        miss_ix = (1 - m_in[..., 0]).permute(0, 2, 1)
        batch_unknown_nodes = torch.nonzero(node_in == 0).flatten().tolist()
        xc, comb = self.data_pre.complete(adj, x_bnt, batch_unknown_nodes, miss_ix)
        return xc.permute(0, 2, 1).unsqueeze(-1), comb.permute(0, 2, 1).unsqueeze(-1)

    def forward(self, r_in, m_in, node_in, cal_in, cal_out, A_q, A_h, adj, xy=None):
        """E14 forward. r_in, m_in (B, T, N, 1); node_in (N,); cal_in (B, T, N, 5); cal_out (B, H, N, 5); A_q, A_h cached random
        walks; adj the method's graph (zero diagonal) for the experts; xy (N, 2) in S1, None in S0. Returns (ŷ (B, H, N, 1)
        standardised factor, r_c)."""
        if self.mode != "masked":
            raise RuntimeError("forward is the masked (E14) mode only")
        B, T, N, _ = r_in.shape
        r_c, _ = self.complete_masked(adj, r_in, m_in, node_in)
        exo_in = [m_in, cal_in]
        node_b = node_in.view(1, N, 1).expand(B, N, 1)
        if xy is not None:
            exo_in.append(xy.view(1, 1, N, 2).expand(B, T, N, 2))
            xy_b = xy.view(1, N, 2).expand(B, N, 2)
        enc_x = torch.cat([r_c] + exo_in, dim=-1)
        if enc_x.shape[-1] != 1 + self.exo_channels:
            raise ValueError(f"encoder input has {enc_x.shape[-1]} channels, the model expects {1 + self.exo_channels}")
        h = self.seq2seq.encoder(enc_x, A_q, A_h)

        def exogenous(t):
            parts = [node_b, cal_out[:, t]]
            if xy is not None:
                parts.append(xy_b)
            return torch.cat(parts, dim=-1)
        out = self.seq2seq.decoder.forward_masked(r_c[:, -1], h, A_q, A_h, exogenous)
        return out, r_c


def exo_channels(regime):
    """Exogenous channels of the adapter: m_in (1) + calendar (5) (+ coordinates (2) in S1)."""
    return 6 + (2 if regime == "S1" else 0)


def build(regime, pred_len=8, input_len=12):
    return MoGERNN(input_len=input_len, pred_len=pred_len, d_model=64, e_layers=2, k_hop=1, num_used_experts=3,
                   exo_channels=exo_channels(regime), mode="masked")


def build_original(pred_len=12, input_len=12):
    return MoGERNN(input_len=input_len, pred_len=pred_len, d_model=64, e_layers=2, k_hop=1, num_used_experts=3, exo_channels=0, mode="original")


# ---------------------------------------------------------------- the method's graph (ADAPTER_SPEC §6) -----

ROAD_RADIUS_M = 2000.0      # declared adaptation (ADAPTER_SPEC §6, decision note of 2026-11-24): pairs farther than this along the road network are not connected


def method_graph(graph, kept, kappa=0.1, radius_m=ROAD_RADIUS_M):
    """The method's graph: Gaussian kernel on road-network distance. d_ij = shortest-path length (metres, edge attribute `weight`)
    on the aligned road graph between kept sensors; pairs with d_ij > `radius_m` are treated as not connected (d = ∞) BEFORE σ is
    estimated — our declared adaptation, a common road radius for the three cities chosen after the inspection of the topology
    and before any fit, to keep the exchanges local (without it σ is dominated by the far pairs and the graph is dense,
    density ≈ 0.4); σ = standard deviation of the finite d_ij, the diagonal zeros included; A_ij = exp(−(d_ij/σ)²) (the Gaussian
    transformation of DCRNN's `gen_adj_mx.py`, which likewise initialises the distances to ∞ and takes σ on the finite ones);
    entries below kappa (0.1) set to 0, so the effective radius is σ·sqrt(ln(1/kappa)) ≤ radius_m; zero diagonal. Built from
    topology only. Returns A (float32), σ, the distance matrix (∞ beyond the radius) and a dict of descriptive statistics
    (density, degree median / min, isolated nodes, the longest surviving edge in metres)."""
    pos = {s: i for i, s in enumerate(kept)}
    K = len(kept)
    D = np.full((K, K), np.inf)
    for src, lengths in nx_all_pairs(graph):
        i = pos[src]
        for dst, d in lengths.items():
            if d <= radius_m:
                D[i, pos[dst]] = d
    finite = D[np.isfinite(D)]
    sigma = float(finite.std())
    A = np.exp(-np.square(D / sigma))
    A[~np.isfinite(D)] = 0.0
    A[A < kappa] = 0.0
    np.fill_diagonal(A, 0.0)
    deg = (A > 0).sum(1); surviving = D[(A > 0)]
    stats = {"radius_m": float(radius_m), "kappa": float(kappa), "sigma_m": sigma, "nodes": int(K), "nonzero_pairs": int((A > 0).sum()),
             "density": float((A > 0).mean()), "degree_median": float(np.median(deg)), "degree_min": int(deg.min()), "isolated_nodes": int((deg == 0).sum()),
             "max_edge_m": float(surviving.max()) if surviving.size else 0.0, "effective_radius_m": float(sigma * np.sqrt(np.log(1 / kappa)))}
    return A.astype("float32"), sigma, D, stats


def nx_all_pairs(graph):
    import networkx as nx
    return nx.all_pairs_dijkstra_path_length(graph, weight="weight")


# ---------------------------------------------------------------- C0.5(a): boolean dependency propagation ---

def _bool_mm(S, X):
    """Boolean matrix product (S: (N, N), X: (N, M)) via a float64 product of 0/1 matrices (counts are exact)."""
    return (S.astype("float64") @ X.astype("float64")) > 0.5


def completion_support(A, inp, completed=None):
    """Structural support of the experts' completion, union over the five experts, restricted to the input nodes' columns:
    mean / weighted mean / diffusion-A_q read the ROW of the adjacency without self-loops (node l depends on k with A[l, k] > 0),
    max / min / diffusion-A_h read the COLUMN (A[k, l] > 0); only input nodes contribute (the unknown columns are zeroed in every
    expert); the gating network reads each node's own series, which is non-zero for input nodes only, so the identity is added
    for input nodes. The completion enters a node's series only where m_in = 0: for a non-input node everywhere, for an input node
    at its missing steps. `completed` (N,) bool marks the nodes whose series receives the completion somewhere in the window
    (default: the non-input nodes only, i.e. no missing reading on any input node); an input node not in `completed` keeps its own
    series exactly and depends on itself only. Returns D_comp (N, n_in) bool and the input nodes' indices."""
    A = np.asarray(A); N = len(A); idx = np.flatnonzero(inp)
    comp = ~np.asarray(inp, dtype=bool) if completed is None else (np.asarray(completed, dtype=bool) | ~np.asarray(inp, dtype=bool))
    nb = (A > 0) | (A.T > 0)
    np.fill_diagonal(nb, False)
    D = nb[:, idx] & comp[:, None]
    D[idx, np.arange(len(idx))] = True
    return D, idx


def cell_support(A):
    """One-hop support S of a DCRNN cell's gates: each DiffConv of order 1 reads I, A_q (rows of A) and A_h (rows of Aᵀ), hence
    S = I ∪ [A > 0] ∪ [Aᵀ > 0]. Returns S and S². Inside a cell the reset gate r = σ(S·[x; h]) multiplies h before the candidate
    c = tanh(S·[x; r·h]), and h' = u·h + (1 − u)·c with u = σ(S·[x; h]): with a non-zero hidden state deps(h') = S²·(deps x ∪ deps h)
    (two convolutions compose through r·h; S² ⊇ S ⊇ I covers the untouched part u·h); with the hidden state identically zero (the
    first recurrent step of a layer) r·h ≡ 0 and u·h ≡ 0, so deps(h') = S·deps(x): one hop only."""
    A = np.asarray(A); N = len(A)
    S = np.eye(N, dtype=bool) | (A > 0) | (A.T > 0)
    return S, _bool_mm(S, S)


def dependency_rows(A, inp, T_in=12, H=8, layers=2, completed=None):
    """Boolean dependency of each decoder output on the input nodes' series, composed in the order of the forward pass:
    completion (`completion_support`) → encoder (T_in steps × `layers` cells) → decoder (H steps × `layers` cells, the output
    re-entering as the next step's factor input), with the cell rule of `cell_support`: one hop at a layer's first step (zero
    hidden state), two hops afterwards. D_h[n, j] = True iff output h of node n can structurally depend on input node j.
    Upper bound of the architecture's information path on 0/1 patterns (no weights, no activations): an EMPTY row excludes a
    dependence; a NON-EMPTY row does not demonstrate one (the secondary classification of E14 is therefore "dependency possible /
    dependency excluded", not "reached / unreached"). Returns the list [D_1 … D_H] (bool (N, n_in)) and the input indices."""
    D_comp, idx = completion_support(A, inp, completed)
    S, S2 = cell_support(A)
    Hs = [None for _ in range(layers)]                                  # None = hidden state identically zero (no step yet)

    def step(x):
        for layer in range(layers):
            Hs[layer] = _bool_mm(S, x) if Hs[layer] is None else _bool_mm(S2, x | Hs[layer])
            x = Hs[layer]
        return x
    for _ in range(T_in):
        step(D_comp)
    out = []
    x = D_comp
    for _ in range(H):
        x = step(x)
        out.append(x.copy())
    return out, idx


def hop_distance_undirected(A, inp):
    """BFS hop distance on A ∪ Aᵀ from the input nodes (−1 = no path)."""
    A = np.asarray(A); n = len(A); und = (A > 0) | (A.T > 0)
    nbrs = [np.flatnonzero(und[m]) for m in range(n)]
    d = np.full(n, -1); q = deque()
    for m in np.flatnonzero(inp):
        d[m] = 0; q.append(m)
    while q:
        m = q.popleft()
        for k in nbrs[m]:
            if d[k] < 0:
                d[k] = d[m] + 1; q.append(k)
    return d


def reference_mass(A_q, inp, hops=14):
    """Σ_{k≤hops} (A_q)^k over the input nodes (float64): the declared REFERENCE linear operator of C0.2 — not the model's
    propagation. Returns the mass per node and the operator restricted to the input columns."""
    Aq = np.asarray(A_q, dtype="float64"); M = np.zeros_like(Aq); P = np.eye(len(Aq))
    for _ in range(hops):
        P = P @ Aq; M = M + P
    return M @ np.asarray(inp, dtype="float64"), M[:, np.flatnonzero(inp)]

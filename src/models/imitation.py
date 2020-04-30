import torch
import torch.nn as nn
from torch.nn import functional as F

from src.constants import HEIGHT, WIDTH, CHANNELS


class ImitationRNNModel(nn.Module):
    HIDDEN_LSTM_UNITS = 100
    OUTPUT_CNN_UNITS = 128

    def __init__(self, out_features: int, num_continuous: int):
        super().__init__()

        self.out_features = out_features
        self.num_continuous = num_continuous

        self.cnn = CNN(self.OUTPUT_CNN_UNITS)
        self.lstm = nn.LSTM(input_size=self.OUTPUT_CNN_UNITS, hidden_size=self.HIDDEN_LSTM_UNITS, batch_first=True)
        self.fc = nn.Linear(in_features=self.HIDDEN_LSTM_UNITS, out_features=out_features)

    def forward(self, pov):
        batch_size = pov.size(0)
        seq_len = pov.size(1)

        # Flatten among batch and sequence dimensions
        pov = pov.view(-1, CHANNELS, WIDTH, HEIGHT)
        pov = self.cnn(pov)
        # Reshape back batch and sequence dimensions
        pov = pov.view(batch_size, seq_len, self.OUTPUT_CNN_UNITS)

        _, (h_n, _) = self.lstm(pov)

        out = F.relu(h_n)
        out = self.fc(out)

        # Set binary outputs in range [0, 1]
        out[:, :, self.num_continuous:] = torch.sigmoid(out[:, :, self.num_continuous:])

        return out


class ImitationCNNModel(nn.Module):
    OUTPUT_CNN_UNITS = 128

    def __init__(self, out_features: int, num_continuous: int):
        super().__init__()

        self.out_features = out_features
        self.num_continuous = num_continuous

        self.cnn = CNN(output_units=self.OUTPUT_CNN_UNITS)
        self.fc = nn.Linear(in_features=self.OUTPUT_CNN_UNITS, out_features=out_features)

    def forward(self, pov):
        out = self.cnn(pov)

        out = F.relu(out)
        out = self.fc(out)

        # Set binary outputs in range [0, 1]
        out[:, self.num_continuous:] = torch.sigmoid(out[:, self.num_continuous:])

        return out


class CNN(nn.Module):
    def __init__(self, output_units: int):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3),
            nn.ReLU(),
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.ReLU(),

            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3),
            nn.ReLU(),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.ReLU(),
        )

        self.fc = nn.Sequential(
            nn.Linear(21632, 500),
            nn.ReLU(),
            nn.Linear(in_features=500, out_features=output_units)
        )

    def forward(self, x):
        bs = x.size(0)
        x = self.cnn(x)
        x = x.view(bs, -1)
        x = self.fc(x)
        return x

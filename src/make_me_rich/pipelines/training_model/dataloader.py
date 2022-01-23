import pandas as pd
import pytorch_lightning as pl

from torch.utils.data import DataLoader
from typing import List, Tuple

from .crypto_dataset import CryptoDataset


class LSTMDataLoader(pl.LightningDataModule):
    """
    Data loader for the LSTM model.
    """
    def __init__(self,
        train_sequences: List[Tuple[pd.DataFrame, float]],
        val_sequences: List[Tuple[pd.DataFrame, float]],
        test_sequences: List[Tuple[pd.DataFrame, float]],
        train_batch_size: int,
        val_batch_size: int,
        train_workers: int = 2,
        val_workers: int = 1,
    ):
        super().__init__()
        self.train_sequences = train_sequences
        self.val_sequences = val_sequences
        self.test_sequences = test_sequences
        self.train_batch_size = train_batch_size
        self.val_batch_size = val_batch_size
        self.train_workers = train_workers
        self.val_workers = val_workers
        self.test_workers = val_workers


    def setup(self, stage: str = None):
        """
        Load the data.
        """
        self.train_dataset = CryptoDataset(self.train_sequences)
        self.val_dataset = CryptoDataset(self.val_sequences)
        self.test_dataset = CryptoDataset(self.test_sequences)

    
    def train_dataloader(self):
        return DataLoader(
            self.train_dataset, 
            batch_size=self.train_batch_size, 
            shuffle=False,
            num_workers=self.train_workers
        )


    def val_dataloader(self):
        return DataLoader(
            self.val_dataset, 
            batch_size=self.val_batch_size, 
            shuffle=False,
            num_workers=self.val_workers
        )


    def test_dataloader(self):
        return DataLoader(
            self.test_dataset, 
            batch_size=self.val_batch_size, 
            shuffle=False,
            num_workers=self.test_workers
        )

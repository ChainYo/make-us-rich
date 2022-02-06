import numpy as np
import os
import onnxruntime
import torch

from datetime import datetime
from dotenv import load_dotenv
from minio import Minio
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from typing import List, Set

from model import OnnxModel


load_dotenv()


class ModelLoader:
    """
    Loader class for interacting with the Minio Object Storage API.
    """

    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False
        )
        self.bucket = os.getenv("MINIO_BUCKET")
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
        self.session_models = {}
        self.storage_path = Path("./models")
        self.update_date()
        self.update_model_files()


    def get_predictions(self, model_name: str, sample) -> None:
        """
        Gets the predictions from the model.

        Parameters
        ----------
        model_name: str
            Name of the model.
        """
        if self._check_model_exists_in_session(model_name):
            model = self.session_models[model_name]["model"]
            return model.predict(sample)
        else:
            raise ValueError("Model not found in session.")


    def update_date(self):
        """
        Updates the date of the loader.
        """
        self.date = datetime.now().strftime("%Y-%m-%d")


    def update_model_files(self):
        """
        Updates the model files in the serving models directory.
        """
        for model in self._get_list_of_available_models():
            currency, compare = model.split("_")
            self._download_files(currency, compare)
            self._add_model_to_session_models(currency, compare)


    def _get_models_files_path(self, currency: str, compare: str):
        """
        Returns the path to the files in models directory.

        Parameters
        ----------
        currency: str
            Currency used in the model.
        compare: str
            Compare used in the model.
        
        Returns
        -------
        str
            Path to the model files.
        """
        model = self.storage_path.joinpath(f"{currency}_{compare}", "model.onnx")
        scaler = self.storage_path.joinpath(f"{currency}_{compare}", "scaler.pkl")
        return model, scaler

    
    def _makedir(self, currency: str, compare: str) -> None:
        """
        Creates a directory for the model files if it doesn't exist.

        Parameters
        ----------
        currency: str
            Currency used in the model.
        compare: str
            Compare used in the model.
        """
        self.storage_path.joinpath(f"{currency}_{compare}").mkdir(exist_ok=True)


    def _download_files(self, currency: str, compare: str) -> None:
        """
        Downloads model and features engineering files from Minio.

        Parameters
        ----------
        currency: str
            Currency used in the model.
        compare: str
            Compare used in the model.
        """
        self._makedir(currency, compare)
        self.client.fget_object(
            self.bucket,
            f"{self.date}/{currency}_{compare}/model.onnx",
            f"{self.storage_path}/{currency}_{compare}/model.onnx"
        )
        self.client.fget_object(
            self.bucket,
            f"{self.date}/{currency}_{compare}/scaler.pkl",
            f"{self.storage_path}/{currency}_{compare}/scaler.pkl"
        )


    def _get_list_of_available_models(self) -> List[Set[str]]:
        """
        Looks for available models in the Minio bucket based on the date.

        Returns
        -------
        List[Set[str]]
            List of available models.
        """
        available_models = self.client.list_objects(self.bucket, prefix=self.date, recursive=True)
        return list(set([model.object_name.split("/")[1] for model in available_models]))

    
    def _add_model_to_session_models(self, currency: str, compare: str) -> str:
        """
        Adds a new model to the model session.

        Parameters
        ----------
        currency: str
            Currency used in the model.
        compare: str
            Compare used in the model.
        
        Returns
        -------
        str
        """
        model_path, scaler_path = self._get_models_files_path(currency, compare)
        model = OnnxModel(model_path=model_path, scaler_path=scaler_path)
        self.session_models[f"{currency}_{compare}"] = {"model": model}
        return f"Model {model} added to session."


    def _check_model_exists_in_session(self, model_name: str) -> bool:
        """
        Checks if the model exists in the session.

        Parameters
        ----------
        model_name: str
            Name of the model.
        
        Returns
        -------
        bool
        """
        if model_name in self.session_models.keys():
            return True
        return False

    
    def _to_numpy(tensor: torch.Tensor):
        """
        Converts a tensor to numpy.

        Parameters
        ----------
        tensor: torch.Tensor
            Tensor to be converted.
        
        Returns
        -------
        numpy.ndarray
        """
        return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()
import joblib
import os
import numpy as np
from typing import Any, Dict
from aquilia.mlops.api.model_class import AquiliaModel, model
from .blueprints import IrisInputBlueprint, IrisOutputBlueprint

@model(name="iris-classifier", version="v1.0.0")
class IrisModel(AquiliaModel):
    """
    Iris Classifier using Scikit-Learn.
    """
    
    async def load(self, artifacts_dir: str, device: str):
        """Load the joblib model from the unpacked artifacts."""
        model_path = os.path.join(artifacts_dir, "model.joblib")
        if not os.path.exists(model_path):
            model_path = os.path.join(artifacts_dir, "model", "model.joblib")
            
        self._clf = joblib.load(model_path)
        print(f"Loaded sklearn model from {model_path}")

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform inference using the loaded classifier."""
        # Convert dict input to feature array
        features = np.array([[
            inputs.get("sepal_length", 0.0),
            inputs.get("sepal_width", 0.0),
            inputs.get("petal_length", 0.0),
            inputs.get("petal_width", 0.0),
        ]])
        
        # Predict class
        species = int(self._clf.predict(features)[0])
        # Get probabilities
        probabilities = self._clf.predict_proba(features)[0].tolist()
        
        return {
            "species": species,
            "probability": probabilities
        }

    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Basic validation before prediction."""
        # Blueprints handle most validation, but we can do extra here if needed
        return inputs

    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Format outputs or add metadata."""
        return outputs

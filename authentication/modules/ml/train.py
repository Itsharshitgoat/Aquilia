import joblib
import os
import asyncio
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from aquilia.mlops.pack.builder import ModelpackBuilder
from aquilia.mlops._types import TensorSpec

async def train_and_pack():
    print("Loading Iris dataset...")
    iris = load_iris()
    X, y = iris.data, iris.target

    print("Training RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    # Save model temporarily
    model_dir = "temp_model"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.joblib")
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

    # Pack using MLOps Builder
    print("Packing model into .aquilia artifact...")
    builder = ModelpackBuilder(name="iris-classifier", version="v1.0.0")
    builder.add_model(model_path, framework="sklearn")
    
    # Define signature
    builder.set_signature(
        inputs=[
            TensorSpec("sepal_length", "float32", [1]),
            TensorSpec("sepal_width", "float32", [1]),
            TensorSpec("petal_length", "float32", [1]),
            TensorSpec("petal_width", "float32", [1]),
        ],
        outputs=[
            TensorSpec("species", "int64", [1]),
            TensorSpec("probability", "float32", [3]),
        ]
    )
    
    # Save to artifacts directory
    output_dir = "../../artifacts/models"
    os.makedirs(output_dir, exist_ok=True)
    pack_path = await builder.save(output_dir)
    print(f"Artifact created: {pack_path}")

    # Cleanup temp
    os.remove(model_path)
    os.rmdir(model_dir)

if __name__ == "__main__":
    asyncio.run(train_and_pack())

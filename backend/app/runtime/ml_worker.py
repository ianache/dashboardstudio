import sys
import json
import argparse
import joblib
import sklearn
import pandas as pd
import warnings

# Suppress sklearn warnings during inspection
warnings.filterwarnings("ignore")

def main():
    parser = argparse.ArgumentParser(description="Isolated ML Worker for Dashboard Studio")
    parser.add_argument("--mode", choices=["inspect", "predict"], required=True)
    parser.add_argument("--model-path", required=True)
    
    args = parser.parse_args()
    
    try:
        if args.mode == "inspect":
            inspect_model(args.model_path)
        elif args.mode == "predict":
            predict_model(args.model_path)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

def inspect_model(model_path):
    """
    Loads a model and extracts metadata: sklearn version and feature names.
    """
    try:
        model = joblib.load(model_path)
        
        # Extract features (standard in sklearn 1.0+)
        features = []
        if hasattr(model, "feature_names_in_"):
            features = list(model.feature_names_in_)
        elif hasattr(model, "n_features_in_"):
            # If names aren't available, at least provide indices
            features = [f"feature_{i}" for i in range(model.n_features_in_)]
            
        metadata = {
            "sklearn_version": sklearn.__version__,
            "features": features
        }
        
        print(json.dumps(metadata))
        
    except Exception as e:
        print(json.dumps({"error": f"Failed to inspect model: {str(e)}"}))
        sys.exit(1)

def predict_model(model_path):
    """
    Reads JSON from stdin, predicts using the model, and prints results.
    """
    try:
        # 1. Load model
        model = joblib.load(model_path)
        
        # 2. Read input from stdin
        input_data = json.load(sys.stdin)
        
        # 3. Prepare DataFrame
        if isinstance(input_data, list):
            df = pd.DataFrame(input_data)
        else:
            df = pd.DataFrame([input_data])
            
        # 4. Predict
        predictions = model.predict(df)
        
        # 5. Output results
        print(json.dumps(predictions.tolist()))
        
    except Exception as e:
        print(json.dumps({"error": f"Inference failed: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()

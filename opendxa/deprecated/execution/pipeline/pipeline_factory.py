"""Example pipeline step implementations.

This module provides fundamental pipeline step patterns and examples.
"""

from typing import Dict, Any, Callable, List, Optional
import asyncio
from datetime import datetime
import json
import numpy as np
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.execution import ExecutionFactory
from opendxa.execution.pipeline.pipeline import Pipeline

class PipelineFactory(ExecutionFactory, Loggable):
    """Factory for creating pipelines."""

    graph_class = Pipeline

    class Steps:
        """Collection of fundamental pipeline steps and examples."""

        # Core Data Flow Steps
        @staticmethod
        async def identity(data: Dict[str, Any]) -> Dict[str, Any]:
            """Pass through data unchanged.
            
            Useful for testing or as a placeholder.
            """
            return data

        @staticmethod
        async def merge(*inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Merge multiple input dictionaries.
            
            Useful for combining data from multiple upstream nodes.
            """
            result = {}
            for data in inputs:
                result.update(data)
            return result

        @staticmethod
        async def split(data: Dict[str, Any], keys: List[str]) -> List[Dict[str, Any]]:
            """Split data into multiple dictionaries by keys.
            
            Useful for routing different parts of data to different downstream nodes.
            """
            return [{key: data[key]} for key in keys if key in data]

        # Data Transformation Steps
        @staticmethod
        async def select(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
            """Select specific keys from data.
            
            Like SQL SELECT or projection.
            """
            return {k: v for k, v in data.items() if k in keys}

        @staticmethod
        async def rename(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
            """Rename keys in data.
            
            Args:
                data: Input data
                mapping: Dict of old_key: new_key pairs
            """
            return {mapping.get(k, k): v for k, v in data.items()}

        @staticmethod
        async def transform(data: Dict[str, Any], 
                            func: Callable[[Any], Any],
                            keys: Optional[List[str]] = None) -> Dict[str, Any]:
            """Apply transformation function to values.
            
            Args:
                data: Input data
                func: Transform function to apply
                keys: Optional list of keys to transform (all if None)
            """
            if keys is None:
                keys = list(data.keys())
            return {
                k: func(v) if k in keys else v 
                for k, v in data.items()
            }

        # Filtering Steps
        @staticmethod
        async def filter_keys(data: Dict[str, Any], 
                              predicate: Callable[[str, Any], bool]) -> Dict[str, Any]:
            """Filter key-value pairs based on predicate.
            
            Args:
                data: Input data
                predicate: Function(key, value) -> bool
            """
            return {
                k: v for k, v in data.items() 
                if predicate(k, v)
            }

        @staticmethod
        async def filter_nulls(data: Dict[str, Any]) -> Dict[str, Any]:
            """Remove keys with None values."""
            return {k: v for k, v in data.items() if v is not None}

        # I/O Steps
        @staticmethod
        async def to_json(data: Dict[str, Any]) -> Dict[str, Any]:
            """Convert data to JSON string."""
            return {"json": json.dumps(data)}

        @staticmethod
        async def from_json(data: Dict[str, Any]) -> Dict[str, Any]:
            """Parse JSON string from data."""
            if "json" not in data:
                raise ValueError("Input must contain 'json' key")
            return json.loads(data["json"])

        # Monitoring Steps
        @staticmethod
        async def log(data: Dict[str, Any], level: str = "INFO") -> Dict[str, Any]:
            """Log data and pass through.
            
            Useful for debugging and monitoring.
            """
            DXA_LOGGER.log(level, "Pipeline data snapshot", 
                           data_keys=list(data.keys()),
                           data_types={k: type(v).__name__ for k, v in data.items()})
            return data

        @staticmethod
        async def add_timestamp(data: Dict[str, Any]) -> Dict[str, Any]:
            """Add timestamp to data."""
            return {
                **data,
                "timestamp": datetime.now().isoformat()
            }

        # Example Implementation Steps
        @staticmethod
        # pylint: disable=unused-argument
        async def sensor_reader(data: Dict[str, Any]) -> Dict[str, Any]:
            """Example source step."""
            DXA_LOGGER.debug("Reading sensor data")
            await asyncio.sleep(0.1)
            return {
                "temperature": 25.0,
                "timestamp": datetime.now().isoformat()
            }

        @staticmethod
        async def analyzer(data: Dict[str, Any]) -> Dict[str, Any]:
            """Example transform step."""
            DXA_LOGGER.debug("Analyzing sensor data", temp=data["temperature"])
            temp = data["temperature"]
            return {
                **data,
                "status": "normal" if 20 <= temp <= 30 else "warning",
                "analyzed_at": datetime.now().isoformat()
            }

        @staticmethod
        async def filter_warnings(data: Dict[str, Any]) -> Dict[str, Any]:
            """Only pass through warning status.
            
            Example of a filter step.
            
            Args:
                data: Input data containing status
                
            Returns:
                Input data if status is warning, empty dict otherwise
            """
            if data["status"] == "warning":
                return data
            return {}

        @staticmethod
        async def reporter(data: Dict[str, Any]) -> Dict[str, Any]:
            """Format data for reporting.
            
            Example of a sink step that formats output.
            
            Args:
                data: Input data to format
                
            Returns:
                Formatted report dict
            """
            return {
                "report": {
                    "temperature": data["temperature"],
                    "status": data["status"],
                    "generated": datetime.now().isoformat()
                }
            } 

        @staticmethod
        async def sklearn_model(data: Dict[str, Any],
                                model: Any,
                                input_key: str = "features",
                                output_key: str = "prediction") -> Dict[str, Any]:
            """Run scikit-learn model prediction.
            
            Args:
                data: Input data containing features
                model: Fitted scikit-learn model instance
                input_key: Key for input features
                output_key: Key for prediction output
            """
            features = data[input_key]
            if not hasattr(features, "reshape"):
                features = np.array(features)
            prediction = model.predict(features.reshape(1, -1))[0]
            return {**data, output_key: prediction}

        @staticmethod
        async def torch_model(data: Dict[str, Any],
                              model: Any,
                              input_key: str = "features",
                              output_key: str = "prediction") -> Dict[str, Any]:
            """Run PyTorch model prediction.
            
            Args:
                data: Input data containing features
                model: PyTorch model in eval mode
                input_key: Key for input features
                output_key: Key for prediction output
            """
            # pylint: disable=import-outside-toplevel
            import torch
            features = data[input_key]
            if not isinstance(features, torch.Tensor):
                features = torch.tensor(features, dtype=torch.float32)
            with torch.no_grad():
                prediction = model(features.unsqueeze(0))[0]
            return {**data, output_key: prediction.numpy().tolist()}

        @staticmethod
        async def tf_model(data: Dict[str, Any],
                           model: Any,
                           input_key: str = "features",
                           output_key: str = "prediction") -> Dict[str, Any]:
            """Run TensorFlow model prediction.
            
            Args:
                data: Input data containing features
                model: TensorFlow model
                input_key: Key for input features
                output_key: Key for prediction output
            """
            # pylint: disable=import-outside-toplevel
            import tensorflow as tf
            features = data[input_key]
            if not isinstance(features, tf.Tensor):
                features = tf.convert_to_tensor([features], dtype=tf.float32)
            prediction = model(features)[0]
            return {**data, output_key: prediction.numpy().tolist()} 

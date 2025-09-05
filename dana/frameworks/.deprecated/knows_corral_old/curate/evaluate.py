from ragas import metrics
from ragas import evaluate
from ragas import EvaluationDataset
import pandas as pd

metric_list = [metrics.answer_similarity, metrics.answer_relevancy]
df = pd.read_csv("/Users/lam/Desktop/repos/opendxa/opendxa/knows/corral/curate/llm_result.csv")
df = df.rename(columns={"question": "user_input", "answer": "response", "ground_truth": "reference"})
result = evaluate(EvaluationDataset.from_pandas(df), metrics=metric_list)

output_df = result.to_pandas()
output_df["type"] = df["type"]
output_df.to_csv("evaluation_result.csv", index=False)

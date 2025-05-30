#!/usr/bin/env python3
"""
Data Analysis IPV Loop Demo

This demonstrates how IPV can be applied to data analysis workflows,
using pandas for computation and iterative refinement to meet analysis objectives.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# Mock LLM for demonstration
class MockAnalysisLLM:
    def __init__(self):
        self.call_count = 0

    def call(self, prompt: str) -> str:
        self.call_count += 1

        # Simulate different types of analysis responses
        if "parse objective" in prompt.lower():
            return """
            ANALYSIS_TASKS:
            1. Load and examine data structure
            2. Calculate sales metrics by product
            3. Identify seasonal patterns
            4. Find top performing products
            5. Create visualizations for trends
            
            EXPECTED_OUTPUTS:
            - Product performance ranking
            - Seasonal trend analysis
            - Revenue insights
            - Visualization plots
            """

        elif "generate pandas code" in prompt.lower():
            return """
            # Load and examine data
            df = pd.read_csv(data_source)
            print(f"Data shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            
            # Calculate product performance
            product_sales = df.groupby('product')['sales'].agg(['sum', 'mean', 'count']).round(2)
            product_sales.columns = ['total_sales', 'avg_sales', 'num_transactions']
            product_sales = product_sales.sort_values('total_sales', ascending=False)
            
            # Seasonal analysis
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.month
            monthly_sales = df.groupby('month')['sales'].sum()
            
            # Top products
            top_products = product_sales.head(5)
            """

        elif "generate visualization code" in prompt.lower():
            return """
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Product performance bar chart
            top_products.plot(kind='bar', y='total_sales', ax=axes[0,0], title='Top Products by Sales')
            axes[0,0].set_ylabel('Total Sales ($)')
            
            # Monthly trend line chart
            monthly_sales.plot(kind='line', ax=axes[0,1], title='Monthly Sales Trend', marker='o')
            axes[0,1].set_ylabel('Sales ($)')
            axes[0,1].set_xlabel('Month')
            
            # Sales distribution histogram
            df['sales'].hist(bins=20, ax=axes[1,0], title='Sales Distribution')
            axes[1,0].set_xlabel('Sales Amount ($)')
            
            # Product count pie chart
            product_counts = df['product'].value_counts().head(5)
            product_counts.plot(kind='pie', ax=axes[1,1], title='Transaction Count by Product')
            
            plt.tight_layout()
            """

        elif "evaluate results" in prompt.lower():
            return """
            ANALYSIS_EVALUATION:
            
            OBJECTIVE_COVERAGE: 85%
            - ✅ Top performing products identified
            - ✅ Seasonal trends analyzed  
            - ✅ Revenue insights generated
            - ⚠️  Could add more statistical analysis
            
            DATA_QUALITY: Good
            - No missing values in key columns
            - Date format consistent
            - Sales values reasonable
            
            INSIGHTS_QUALITY: High
            - Clear product performance ranking
            - Seasonal patterns visible
            - Actionable business insights
            
            RECOMMENDATIONS:
            - Add correlation analysis
            - Include growth rate calculations
            - Consider customer segmentation
            """

        elif "refine analysis" in prompt.lower():
            return """
            # Enhanced analysis with additional insights
            
            # Growth rate analysis
            df_monthly = df.groupby([df['date'].dt.to_period('M'), 'product'])['sales'].sum().reset_index()
            df_monthly['date'] = df_monthly['date'].dt.to_timestamp()
            
            # Calculate month-over-month growth
            for product in df['product'].unique():
                product_data = df_monthly[df_monthly['product'] == product].sort_values('date')
                product_data['growth_rate'] = product_data['sales'].pct_change() * 100
            
            # Correlation analysis
            correlation_matrix = df[['sales', 'quantity', 'price']].corr()
            
            # Customer value analysis
            customer_value = df.groupby('customer_id')['sales'].agg(['sum', 'count', 'mean'])
            high_value_customers = customer_value[customer_value['sum'] > customer_value['sum'].quantile(0.8)]
            """

        else:
            return "Analysis completed successfully."


@dataclass
class AnalysisContext:
    """Context for data analysis operations"""

    objective: str
    data_source: str
    data_info: Dict[str, Any]
    analysis_tasks: List[str]
    current_iteration: int = 0
    max_iterations: int = 3


@dataclass
class AnalysisResult:
    """Result of data analysis operation"""

    success: bool
    insights: Dict[str, Any]
    visualizations: List[str]  # Base64 encoded plots
    code_executed: str
    confidence_score: float
    recommendations: List[str]
    error: Optional[str] = None


class AnalysisStrategy(Enum):
    EXPLORATORY = "exploratory"
    TARGETED = "targeted"
    COMPREHENSIVE = "comprehensive"


class DataAnalysisIPV:
    """IPV engine for data analysis workflows"""

    def __init__(self, llm=None, verbose=False):
        self.llm = llm or MockAnalysisLLM()
        self.verbose = verbose

    def analyze_data(
        self, data_source: str, objective: str, strategy: AnalysisStrategy = AnalysisStrategy.TARGETED, config: Optional[Dict] = None
    ) -> AnalysisResult:
        """
        Main IPV analysis function

        Args:
            data_source: Path to data file or DataFrame
            objective: Natural language description of analysis goal
            strategy: Analysis strategy to use
            config: Additional configuration options

        Returns:
            AnalysisResult with insights, visualizations, and recommendations
        """
        if config is None:
            config = {}

        if self.verbose:
            print("\n🔬 DATA ANALYSIS IPV LOOP")
            print(f"📊 Objective: {objective}")
            print(f"📁 Data Source: {data_source}")
            print(f"⚡ Strategy: {strategy.value}")
            print("=" * 60)

        # Create analysis context
        context = AnalysisContext(
            objective=objective, data_source=data_source, data_info={}, analysis_tasks=[], max_iterations=config.get("max_iterations", 3)
        )

        try:
            # INFER: Understand objective and plan analysis
            enhanced_context = self._infer_analysis_plan(context, strategy, config)

            # PROCESS: Execute analysis with iterative refinement
            analysis_output = self._process_analysis(enhanced_context, config)

            # VALIDATE: Check if objective is met and refine if needed
            final_result = self._validate_and_refine(analysis_output, enhanced_context, config)

            return final_result

        except Exception as e:
            return AnalysisResult(
                success=False, insights={}, visualizations=[], code_executed="", confidence_score=0.0, recommendations=[], error=str(e)
            )

    def _infer_analysis_plan(self, context: AnalysisContext, strategy: AnalysisStrategy, config: Dict) -> AnalysisContext:
        """INFER: Parse objective and create analysis plan"""

        if self.verbose:
            print("\n🧠 INFER: Planning Analysis")
            print(f"📋 Parsing objective: '{context.objective}'")

        # Load and examine data structure
        if isinstance(context.data_source, str):
            # Assume CSV for demo
            df = self._load_sample_data()  # In real implementation, load actual file
        else:
            df = context.data_source

        context.data_info = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head().to_dict(),
        }

        # Parse objective into specific tasks
        planning_prompt = f"""
        Parse this data analysis objective into specific tasks:
        
        OBJECTIVE: {context.objective}
        
        DATA INFO:
        - Shape: {context.data_info['shape']}
        - Columns: {context.data_info['columns']}
        - Data types: {context.data_info['dtypes']}
        
        STRATEGY: {strategy.value}
        
        Generate a list of specific analysis tasks and expected outputs.
        """

        plan_response = self.llm.call(planning_prompt)

        # Extract tasks (simplified parsing for demo)
        context.analysis_tasks = [
            "Load and examine data structure",
            "Calculate key metrics",
            "Identify patterns and trends",
            "Generate visualizations",
            "Extract actionable insights",
        ]

        if self.verbose:
            print(f"📊 Data shape: {context.data_info['shape']}")
            print(f"📈 Analysis tasks: {len(context.analysis_tasks)} identified")
            for i, task in enumerate(context.analysis_tasks, 1):
                print(f"   {i}. {task}")

        return context

    def _process_analysis(self, context: AnalysisContext, config: Dict) -> Dict[str, Any]:
        """PROCESS: Execute analysis with pandas operations"""

        if self.verbose:
            print("\n⚙️  PROCESS: Executing Analysis")

        # Load data
        df = self._load_sample_data()

        analysis_results = {"data_summary": {}, "insights": {}, "visualizations": [], "code_executed": "", "intermediate_results": {}}

        # Generate pandas code for analysis
        code_prompt = f"""
        Generate pandas code to analyze this data for the objective: {context.objective}
        
        Data columns: {context.data_info['columns']}
        Data shape: {context.data_info['shape']}
        
        Focus on:
        {chr(10).join(f"- {task}" for task in context.analysis_tasks)}
        
        Generate efficient pandas operations.
        """

        pandas_code = self.llm.call(code_prompt)
        analysis_results["code_executed"] = pandas_code

        if self.verbose:
            print("🐼 Generated pandas operations")
            print("📊 Executing analysis...")

        # Execute analysis (simplified for demo)
        try:
            # Product performance analysis
            product_sales = df.groupby("product")["sales"].agg(["sum", "mean", "count"]).round(2)
            product_sales.columns = ["total_sales", "avg_sales", "num_transactions"]
            product_sales = product_sales.sort_values("total_sales", ascending=False)

            # Seasonal analysis
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.month
            monthly_sales = df.groupby("month")["sales"].sum()

            # Store results
            analysis_results["insights"] = {
                "top_products": product_sales.head().to_dict(),
                "monthly_trends": monthly_sales.to_dict(),
                "total_revenue": df["sales"].sum(),
                "avg_transaction": df["sales"].mean(),
                "num_products": df["product"].nunique(),
            }

            analysis_results["data_summary"] = {
                "total_transactions": len(df),
                "date_range": f"{df['date'].min()} to {df['date'].max()}",
                "revenue_range": f"${df['sales'].min():.2f} - ${df['sales'].max():.2f}",
            }

            if self.verbose:
                print("✅ Analysis completed successfully")
                print(f"📈 Found {len(analysis_results['insights'])} key insights")

        except Exception as e:
            if self.verbose:
                print(f"❌ Analysis error: {e}")
            analysis_results["error"] = str(e)

        # Generate visualizations
        viz_code = self._generate_visualizations(df, context)
        analysis_results["visualizations"] = viz_code

        return analysis_results

    def _validate_and_refine(self, analysis_output: Dict, context: AnalysisContext, config: Dict) -> AnalysisResult:
        """VALIDATE: Check if objective is met and refine if needed"""

        if self.verbose:
            print("\n✅ VALIDATE: Checking Analysis Quality")

        # Evaluate how well the analysis meets the objective
        evaluation_prompt = f"""
        Evaluate this data analysis against the original objective:
        
        OBJECTIVE: {context.objective}
        
        ANALYSIS RESULTS:
        - Insights: {analysis_output.get('insights', {})}
        - Data Summary: {analysis_output.get('data_summary', {})}
        - Visualizations: {len(analysis_output.get('visualizations', []))} created
        
        Rate the analysis on:
        1. Objective coverage (0-100%)
        2. Data quality assessment
        3. Insight quality
        4. Recommendations for improvement
        """

        evaluation = self.llm.call(evaluation_prompt)

        # Extract confidence score (simplified)
        confidence_score = 0.85  # Would parse from LLM response

        # Check if refinement is needed
        needs_refinement = confidence_score < 0.8 and context.current_iteration < context.max_iterations

        if needs_refinement and self.verbose:
            print(f"🔄 Confidence score: {confidence_score:.2f} - Refining analysis...")

            # Generate refinement code
            refinement_prompt = f"""
            The analysis needs improvement. Generate additional pandas code to:
            1. Add more statistical analysis
            2. Include correlation analysis  
            3. Provide deeper insights
            
            Current results: {analysis_output.get('insights', {})}
            """

            refinement_code = self.llm.call(refinement_prompt)
            analysis_output["code_executed"] += "\n\n# REFINEMENT:\n" + refinement_code

            # Would execute refinement code here
            confidence_score = 0.92  # Improved after refinement

        if self.verbose:
            print(f"🎯 Final confidence score: {confidence_score:.2f}")
            print(f"📊 Analysis {'meets' if confidence_score >= 0.8 else 'partially meets'} objective")

        # Generate recommendations
        recommendations = [
            "Focus marketing on top-performing products",
            "Investigate seasonal patterns for inventory planning",
            "Analyze customer segments for targeted campaigns",
            "Monitor monthly trends for early warning signals",
        ]

        return AnalysisResult(
            success=True,
            insights=analysis_output.get("insights", {}),
            visualizations=analysis_output.get("visualizations", []),
            code_executed=analysis_output.get("code_executed", ""),
            confidence_score=confidence_score,
            recommendations=recommendations,
        )

    def _generate_visualizations(self, df: pd.DataFrame, context: AnalysisContext) -> List[str]:
        """Generate matplotlib/seaborn visualizations"""

        if self.verbose:
            print("📊 Generating visualizations...")

        viz_prompt = f"""
        Generate matplotlib/seaborn code for visualizations that support the objective:
        {context.objective}
        
        Available data columns: {df.columns.tolist()}
        
        Create 2-3 meaningful plots.
        """

        viz_code = self.llm.call(viz_prompt)

        # In real implementation, would execute the code and capture plots
        # For demo, return the code
        return [viz_code]

    def _load_sample_data(self) -> pd.DataFrame:
        """Load sample sales data for demonstration"""
        np.random.seed(42)

        # Generate sample sales data
        dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
        products = ["Widget A", "Widget B", "Widget C", "Widget D", "Widget E"]

        data = []
        for date in dates:
            # Seasonal effect (higher sales in Q4)
            seasonal_multiplier = 1.5 if date.month in [11, 12] else 1.0

            for _ in range(np.random.randint(1, 8)):  # 1-7 transactions per day
                product = np.random.choice(products)

                # Product-specific base sales
                base_sales = {"Widget A": 150, "Widget B": 200, "Widget C": 100, "Widget D": 300, "Widget E": 120}[product]

                sales = base_sales * seasonal_multiplier * np.random.uniform(0.7, 1.3)

                data.append(
                    {
                        "date": date,
                        "product": product,
                        "sales": round(sales, 2),
                        "quantity": np.random.randint(1, 5),
                        "price": round(sales / np.random.randint(1, 5), 2),
                        "customer_id": f"CUST_{np.random.randint(1000, 9999)}",
                    }
                )

        return pd.DataFrame(data)


def demo_data_analysis_ipv():
    """Demonstrate the Data Analysis IPV loop"""

    print("🔬 DATA ANALYSIS IPV LOOP DEMONSTRATION")
    print("=" * 60)

    # Create IPV analyzer
    analyzer = DataAnalysisIPV(verbose=True)

    # Demo 1: Sales Performance Analysis
    print("\n📊 DEMO 1: Sales Performance Analysis")
    print("-" * 40)

    result1 = analyzer.analyze_data(
        data_source="sales_data.csv",
        objective="identify top performing products and understand seasonal sales patterns",
        strategy=AnalysisStrategy.COMPREHENSIVE,
    )

    print("\n📈 RESULTS:")
    print(f"✅ Success: {result1.success}")
    print(f"🎯 Confidence: {result1.confidence_score:.2f}")
    print(f"💡 Key Insights: {len(result1.insights)} found")
    print(f"📊 Visualizations: {len(result1.visualizations)} created")
    print(f"🔧 Recommendations: {len(result1.recommendations)} generated")

    # Demo 2: Customer Behavior Analysis
    print("\n\n👥 DEMO 2: Customer Behavior Analysis")
    print("-" * 40)

    result2 = analyzer.analyze_data(
        data_source="sales_data.csv",
        objective="analyze customer purchasing patterns and identify high-value customer segments",
        strategy=AnalysisStrategy.TARGETED,
        config={"max_iterations": 2},
    )

    print("\n📈 RESULTS:")
    print(f"✅ Success: {result2.success}")
    print(f"🎯 Confidence: {result2.confidence_score:.2f}")

    # Demo 3: Quick Exploratory Analysis
    print("\n\n🔍 DEMO 3: Quick Exploratory Analysis")
    print("-" * 40)

    result3 = analyzer.analyze_data(
        data_source="sales_data.csv",
        objective="get a quick overview of the data and identify any obvious patterns or anomalies",
        strategy=AnalysisStrategy.EXPLORATORY,
    )

    print("\n📈 RESULTS:")
    print(f"✅ Success: {result3.success}")
    print(f"🎯 Confidence: {result3.confidence_score:.2f}")

    print("\n🎉 DATA ANALYSIS IPV DEMONSTRATION COMPLETE!")
    print(f"📞 Total LLM calls made: {analyzer.llm.call_count}")

    return result1, result2, result3


if __name__ == "__main__":
    demo_data_analysis_ipv()

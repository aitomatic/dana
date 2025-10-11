# FinancialAnalyst Implementation Specification

## Overview

The FinancialAnalyst is a specialized agent implementation for financial analysis and market research tasks. It demonstrates how the agentic architecture can be adapted for domain-specific financial workflows, data analysis, and investment research.

## FinancialAnalyst Class

```python
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from ..core.agent import Agent
from ..core.resource import Resource, MethodInfo
from ..core.workflow import Workflow, WorkflowStep
from ..core.prompt_engineer import PromptEngineer

class FinancialAnalyst(Agent):
    """
    Specialized agent for financial analysis and market research.

    Provides capabilities for:
    - Market data retrieval and analysis
    - Financial news and sentiment analysis
    - Company financial statement analysis
    - Portfolio optimization and risk assessment
    - Economic indicator analysis
    - Investment recommendation generation
    """

    def __init__(self,
                 llm_provider: str | None = None,
                 model: str | None = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the FinancialAnalyst.

        Args:
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai')
            model: Model name to use (defaults to provider's default)
            config: Optional configuration dictionary
        """
        # Initialize base agent
        super().__init__('financial_analyst', llm_provider, model, config)

        # Set up financial-specific configuration
        self._setup_financial_config()

        # Register financial resources
        self._setup_financial_resources()

        # Register financial workflows
        self._setup_financial_workflows()

        # Initialize financial-specific state
        self._initialize_financial_state()

    def _setup_financial_config(self) -> None:
        """Set up financial-specific configuration."""
        financial_config = {
            'data_sources': ['yahoo', 'alpha_vantage', 'quandl'],
            'analysis_period': '1y',
            'confidence_threshold': 0.7,
            'risk_tolerance': 'moderate',
            'currency': 'USD',
            'timezone': 'UTC',
            'cache_duration': 3600,  # 1 hour
            'max_portfolio_size': 50,
            'rebalance_frequency': 'monthly',
            'benchmark_index': 'SPY',
            'risk_free_rate': 0.02,
            'market_cap_threshold': 1000000000,  # $1B
            'sector_analysis': True,
            'technical_indicators': True,
            'fundamental_analysis': True,
            'sentiment_analysis': True
        }

        # Merge with existing config
        self.config.update(financial_config)

    def _initialize_financial_state(self) -> None:
        """Initialize financial-specific state."""
        financial_state = {
            'current_portfolio': {},
            'watchlist': [],
            'market_conditions': {},
            'economic_indicators': {},
            'sector_performance': {},
            'risk_metrics': {},
            'analysis_history': [],
            'recommendations': [],
            'alerts': [],
            'market_sentiment': {},
            'currency_rates': {},
            'commodity_prices': {},
            'bond_yields': {},
            'volatility_index': {},
            'trading_volume': {},
            'earnings_calendar': [],
            'dividend_calendar': [],
            'splits_calendar': []
        }

        self.update_state({'financial': financial_state})

    def _setup_financial_resources(self) -> None:
        """Register financial-specific resources."""
        # Market Data Resource
        self.register_resource('market_data', MarketDataResource(self.config))

        # Financial News Resource
        self.register_resource('financial_news', FinancialNewsResource(self.config))

        # Company Data Resource
        self.register_resource('company_data', CompanyDataResource(self.config))

        # Economic Indicators Resource
        self.register_resource('economic_indicators', EconomicIndicatorsResource(self.config))

        # Portfolio Data Resource
        self.register_resource('portfolio_data', PortfolioDataResource(self.config))

        # Sentiment Analysis Resource
        self.register_resource('sentiment_analysis', SentimentAnalysisResource(self.config))

        # Risk Analysis Resource
        self.register_resource('risk_analysis', RiskAnalysisResource(self.config))

    def _setup_financial_workflows(self) -> None:
        """Register financial-specific workflows."""
        # Analyze Stock Workflow
        self.register_workflow('analyze_stock', AnalyzeStockWorkflow(self.config))

        # Portfolio Optimization Workflow
        self.register_workflow('optimize_portfolio', OptimizePortfolioWorkflow(self.config))

        # Risk Assessment Workflow
        self.register_workflow('assess_risk', AssessRiskWorkflow(self.config))

        # Market Research Workflow
        self.register_workflow('market_research', MarketResearchWorkflow(self.config))

        # Earnings Analysis Workflow
        self.register_workflow('earnings_analysis', EarningsAnalysisWorkflow(self.config))

        # Sector Analysis Workflow
        self.register_workflow('sector_analysis', SectorAnalysisWorkflow(self.config))

        # Technical Analysis Workflow
        self.register_workflow('technical_analysis', TechnicalAnalysisWorkflow(self.config))

        # Fundamental Analysis Workflow
        self.register_workflow('fundamental_analysis', FundamentalAnalysisWorkflow(self.config))
```

## Financial Resources

### Market Data Resource

```python
class MarketDataResource(Resource):
    """Resource for market data retrieval and analysis."""

    def __init__(self, config: Dict[str, Any]):
        methods = {
            'get_stock_data': MethodInfo(
                name='get_stock_data',
                docstring='Get historical stock price data',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string', 'description': 'Stock symbol'},
                        'period': {'type': 'string', 'description': 'Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)'},
                        'interval': {'type': 'string', 'description': 'Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)'},
                        'start_date': {'type': 'string', 'description': 'Start date (YYYY-MM-DD)'},
                        'end_date': {'type': 'string', 'description': 'End date (YYYY-MM-DD)'}
                    },
                    'required': ['symbol']
                },
                handler=self._get_stock_data
            ),
            'get_market_summary': MethodInfo(
                name='get_market_summary',
                docstring='Get overall market summary and indices',
                parameters={
                    'type': 'object',
                    'properties': {
                        'indices': {'type': 'array', 'description': 'List of indices to include'},
                        'currency': {'type': 'string', 'description': 'Currency for prices'}
                    }
                },
                handler=self._get_market_summary
            ),
            'get_real_time_price': MethodInfo(
                name='get_real_time_price',
                docstring='Get real-time stock price',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string', 'description': 'Stock symbol'},
                        'currency': {'type': 'string', 'description': 'Currency for price'}
                    },
                    'required': ['symbol']
                },
                handler=self._get_real_time_price
            ),
            'get_technical_indicators': MethodInfo(
                name='get_technical_indicators',
                docstring='Calculate technical indicators for stock data',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string', 'description': 'Stock symbol'},
                        'indicators': {'type': 'array', 'description': 'List of indicators to calculate'},
                        'period': {'type': 'string', 'description': 'Time period for calculation'}
                    },
                    'required': ['symbol', 'indicators']
                },
                handler=self._get_technical_indicators
            )
        }

        super().__init__('market_data', 'Market data retrieval and analysis', methods, config)
        self.data_sources = config.get('data_sources', ['yahoo'])
        self.cache = {}
        self.cache_duration = config.get('cache_duration', 3600)

    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market data operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")

        method_info = self.methods[method]
        start_time = datetime.now()

        try:
            # Check cache first
            cache_key = f"{method}_{hash(str(params))}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_duration:
                    return {
                        'success': True,
                        'result': cached_data,
                        'method': method,
                        'cached': True
                    }

            # Update usage stats
            self.metadata['usage_stats'][method]['calls'] += 1

            # Execute method
            result = method_info.handler(params)

            # Cache result
            self.cache[cache_key] = (result, datetime.now())

            # Update success stats
            self.metadata['usage_stats'][method]['successes'] += 1

            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(method, execution_time)

            return {
                'success': True,
                'result': result,
                'method': method,
                'execution_time': execution_time,
                'cached': False
            }

        except Exception as e:
            # Update error stats
            self.metadata['usage_stats'][method]['errors'] += 1

            return {
                'success': False,
                'error': str(e),
                'method': method,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }

    def _get_stock_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical stock price data."""
        symbol = params['symbol']
        period = params.get('period', '1y')
        interval = params.get('interval', '1d')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        # This would integrate with actual market data APIs
        # For now, return mock data
        mock_data = {
            'symbol': symbol,
            'period': period,
            'interval': interval,
            'data': [
                {'date': '2024-01-01', 'open': 100.0, 'high': 105.0, 'low': 98.0, 'close': 102.0, 'volume': 1000000},
                {'date': '2024-01-02', 'open': 102.0, 'high': 108.0, 'low': 101.0, 'close': 106.0, 'volume': 1200000},
                {'date': '2024-01-03', 'open': 106.0, 'high': 110.0, 'low': 104.0, 'close': 108.0, 'volume': 1100000}
            ],
            'metadata': {
                'currency': 'USD',
                'timezone': 'UTC',
                'data_source': 'yahoo'
            }
        }

        return mock_data

    def _get_market_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall market summary."""
        indices = params.get('indices', ['^GSPC', '^DJI', '^IXIC', '^VIX'])
        currency = params.get('currency', 'USD')

        # This would fetch real market data
        mock_summary = {
            'indices': {
                'S&P 500': {'symbol': '^GSPC', 'price': 4500.0, 'change': 25.0, 'change_percent': 0.56},
                'Dow Jones': {'symbol': '^DJI', 'price': 35000.0, 'change': 150.0, 'change_percent': 0.43},
                'NASDAQ': {'symbol': '^IXIC', 'price': 14000.0, 'change': 80.0, 'change_percent': 0.57},
                'VIX': {'symbol': '^VIX', 'price': 18.5, 'change': -1.2, 'change_percent': -6.09}
            },
            'market_status': 'open',
            'currency': currency,
            'timestamp': datetime.now().isoformat()
        }

        return mock_summary

    def _get_real_time_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time stock price."""
        symbol = params['symbol']
        currency = params.get('currency', 'USD')

        # This would fetch real-time data
        mock_price = {
            'symbol': symbol,
            'price': 150.25,
            'change': 2.15,
            'change_percent': 1.45,
            'volume': 500000,
            'currency': currency,
            'timestamp': datetime.now().isoformat()
        }

        return mock_price

    def _get_technical_indicators(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical indicators."""
        symbol = params['symbol']
        indicators = params['indicators']
        period = params.get('period', '1y')

        # This would calculate actual technical indicators
        mock_indicators = {
            'symbol': symbol,
            'period': period,
            'indicators': {
                'SMA_20': 148.5,
                'SMA_50': 145.2,
                'RSI': 65.4,
                'MACD': 2.1,
                'Bollinger_Upper': 155.0,
                'Bollinger_Lower': 140.0
            },
            'timestamp': datetime.now().isoformat()
        }

        return mock_indicators
```

### Financial News Resource

```python
class FinancialNewsResource(Resource):
    """Resource for financial news and sentiment analysis."""

    def __init__(self, config: Dict[str, Any]):
        methods = {
            'get_news': MethodInfo(
                name='get_news',
                docstring='Get financial news for specific symbols or topics',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbols': {'type': 'array', 'description': 'List of stock symbols'},
                        'topics': {'type': 'array', 'description': 'List of topics to search for'},
                        'limit': {'type': 'integer', 'description': 'Maximum number of articles'},
                        'timeframe': {'type': 'string', 'description': 'Timeframe for news (1h, 24h, 7d, 30d)'},
                        'sentiment': {'type': 'boolean', 'description': 'Include sentiment analysis'}
                    }
                },
                handler=self._get_news
            ),
            'analyze_sentiment': MethodInfo(
                name='analyze_sentiment',
                docstring='Analyze sentiment of financial news',
                parameters={
                    'type': 'object',
                    'properties': {
                        'text': {'type': 'string', 'description': 'Text to analyze'},
                        'symbol': {'type': 'string', 'description': 'Related stock symbol'},
                        'source': {'type': 'string', 'description': 'News source'}
                    },
                    'required': ['text']
                },
                handler=self._analyze_sentiment
            ),
            'get_market_sentiment': MethodInfo(
                name='get_market_sentiment',
                docstring='Get overall market sentiment',
                parameters={
                    'type': 'object',
                    'properties': {
                        'indices': {'type': 'array', 'description': 'List of indices to analyze'},
                        'timeframe': {'type': 'string', 'description': 'Timeframe for analysis'}
                    }
                },
                handler=self._get_market_sentiment
            )
        }

        super().__init__('financial_news', 'Financial news and sentiment analysis', methods, config)

    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute financial news operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")

        method_info = self.methods[method]
        start_time = datetime.now()

        try:
            # Update usage stats
            self.metadata['usage_stats'][method]['calls'] += 1

            # Execute method
            result = method_info.handler(params)

            # Update success stats
            self.metadata['usage_stats'][method]['successes'] += 1

            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(method, execution_time)

            return {
                'success': True,
                'result': result,
                'method': method,
                'execution_time': execution_time
            }

        except Exception as e:
            # Update error stats
            self.metadata['usage_stats'][method]['errors'] += 1

            return {
                'success': False,
                'error': str(e),
                'method': method,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }

    def _get_news(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get financial news."""
        symbols = params.get('symbols', [])
        topics = params.get('topics', [])
        limit = params.get('limit', 10)
        timeframe = params.get('timeframe', '24h')
        sentiment = params.get('sentiment', False)

        # This would fetch real news data
        mock_news = [
            {
                'title': 'Stock Market Rises on Positive Economic Data',
                'summary': 'The stock market closed higher today following positive economic indicators...',
                'url': 'https://example.com/news/1',
                'source': 'Financial Times',
                'published': datetime.now().isoformat(),
                'symbols': ['AAPL', 'MSFT'],
                'sentiment': 'positive' if sentiment else None,
                'sentiment_score': 0.8 if sentiment else None
            },
            {
                'title': 'Tech Stocks Face Volatility Amid Regulatory Concerns',
                'summary': 'Technology stocks experienced significant volatility today...',
                'url': 'https://example.com/news/2',
                'source': 'Wall Street Journal',
                'published': datetime.now().isoformat(),
                'symbols': ['GOOGL', 'META'],
                'sentiment': 'negative' if sentiment else None,
                'sentiment_score': -0.3 if sentiment else None
            }
        ]

        return mock_news[:limit]

    def _analyze_sentiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of financial news."""
        text = params['text']
        symbol = params.get('symbol')
        source = params.get('source')

        # This would use actual sentiment analysis
        mock_sentiment = {
            'text': text,
            'symbol': symbol,
            'source': source,
            'sentiment': 'positive',
            'sentiment_score': 0.7,
            'confidence': 0.85,
            'keywords': ['growth', 'positive', 'strong'],
            'timestamp': datetime.now().isoformat()
        }

        return mock_sentiment

    def _get_market_sentiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall market sentiment."""
        indices = params.get('indices', ['^GSPC', '^DJI', '^IXIC'])
        timeframe = params.get('timeframe', '24h')

        # This would analyze overall market sentiment
        mock_sentiment = {
            'overall_sentiment': 'positive',
            'sentiment_score': 0.6,
            'confidence': 0.8,
            'indices': {
                'S&P 500': {'sentiment': 'positive', 'score': 0.7},
                'Dow Jones': {'sentiment': 'positive', 'score': 0.6},
                'NASDAQ': {'sentiment': 'neutral', 'score': 0.5}
            },
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat()
        }

        return mock_sentiment
```

## Financial Workflows

### Analyze Stock Workflow

```python
class AnalyzeStockWorkflow(Workflow):
    """Workflow for comprehensive stock analysis."""

    def __init__(self, config: Dict[str, Any]):
        steps = [
            WorkflowStep(
                name='fetch_market_data',
                function=fetch_stock_market_data,
                input_mapping={'symbol': 'symbol', 'period': 'period'},
                output_mapping={'price_data': 'price_data', 'volume_data': 'volume_data'}
            ),
            WorkflowStep(
                name='get_company_info',
                function=get_company_information,
                input_mapping={'symbol': 'symbol'},
                output_mapping={'company_info': 'company_info', 'financials': 'financials'}
            ),
            WorkflowStep(
                name='calculate_metrics',
                function=calculate_financial_metrics,
                input_mapping={'price_data': 'price_data', 'financials': 'financials'},
                output_mapping={'metrics': 'metrics', 'ratios': 'ratios'}
            ),
            WorkflowStep(
                name='analyze_news_sentiment',
                function=analyze_news_sentiment,
                input_mapping={'symbol': 'symbol', 'timeframe': 'timeframe'},
                output_mapping={'sentiment': 'sentiment', 'news_summary': 'news_summary'}
            ),
            WorkflowStep(
                name='generate_analysis',
                function=generate_stock_analysis,
                input_mapping={'metrics': 'metrics', 'sentiment': 'sentiment', 'company_info': 'company_info'},
                output_mapping={'analysis': 'analysis', 'recommendation': 'recommendation', 'risk_level': 'risk_level'}
            )
        ]

        super().__init__(
            name='analyze_stock',
            description='Comprehensive stock analysis including technical, fundamental, and sentiment analysis',
            steps=steps,
            config=config
        )

def fetch_stock_market_data(symbol: str, period: str) -> Dict[str, Any]:
    """Fetch stock market data."""
    # This would call the market data resource
    return {
        'price_data': [100, 102, 98, 105, 108],
        'volume_data': [1000000, 1200000, 800000, 1500000, 1100000],
        'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
    }

def get_company_information(symbol: str) -> Dict[str, Any]:
    """Get company information and financials."""
    # This would call the company data resource
    return {
        'company_info': {
            'name': 'Example Corp',
            'sector': 'Technology',
            'industry': 'Software',
            'market_cap': 1000000000,
            'employees': 5000
        },
        'financials': {
            'revenue': 500000000,
            'profit': 50000000,
            'assets': 2000000000,
            'liabilities': 800000000
        }
    }

def calculate_financial_metrics(price_data: List[float], financials: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate financial metrics and ratios."""
    # This would perform actual calculations
    return {
        'metrics': {
            'average_price': sum(price_data) / len(price_data),
            'price_change': price_data[-1] - price_data[0],
            'volatility': 0.15
        },
        'ratios': {
            'pe_ratio': 20.0,
            'pb_ratio': 2.5,
            'debt_to_equity': 0.4,
            'roe': 0.12
        }
    }

def analyze_news_sentiment(symbol: str, timeframe: str) -> Dict[str, Any]:
    """Analyze news sentiment for the stock."""
    # This would call the financial news resource
    return {
        'sentiment': 'positive',
        'sentiment_score': 0.7,
        'news_summary': 'Recent news has been generally positive for this stock'
    }

def generate_stock_analysis(metrics: Dict[str, Any], sentiment: Dict[str, Any], company_info: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive stock analysis."""
    # This would use AI to generate analysis
    return {
        'analysis': 'The stock shows strong fundamentals with positive sentiment',
        'recommendation': 'BUY',
        'risk_level': 'MODERATE',
        'confidence': 0.8
    }
```

### Portfolio Optimization Workflow

```python
class OptimizePortfolioWorkflow(Workflow):
    """Workflow for portfolio optimization."""

    def __init__(self, config: Dict[str, Any]):
        steps = [
            WorkflowStep(
                name='analyze_current_portfolio',
                function=analyze_current_portfolio,
                input_mapping={'portfolio': 'portfolio', 'benchmark': 'benchmark'},
                output_mapping={'current_metrics': 'current_metrics', 'performance': 'performance'}
            ),
            WorkflowStep(
                name='calculate_risk_metrics',
                function=calculate_portfolio_risk,
                input_mapping={'portfolio': 'portfolio', 'market_data': 'market_data'},
                output_mapping={'risk_metrics': 'risk_metrics', 'correlation_matrix': 'correlation_matrix'}
            ),
            WorkflowStep(
                name='optimize_weights',
                function=optimize_portfolio_weights,
                input_mapping={'portfolio': 'portfolio', 'risk_metrics': 'risk_metrics', 'constraints': 'constraints'},
                output_mapping={'optimized_weights': 'optimized_weights', 'expected_return': 'expected_return', 'expected_risk': 'expected_risk'}
            ),
            WorkflowStep(
                name='generate_rebalancing_plan',
                function=generate_rebalancing_plan,
                input_mapping={'current_weights': 'portfolio', 'optimized_weights': 'optimized_weights'},
                output_mapping={'rebalancing_plan': 'rebalancing_plan', 'transaction_costs': 'transaction_costs'}
            )
        ]

        super().__init__(
            name='optimize_portfolio',
            description='Optimize portfolio allocation using modern portfolio theory',
            steps=steps,
            config=config
        )

def analyze_current_portfolio(portfolio: Dict[str, Any], benchmark: str) -> Dict[str, Any]:
    """Analyze current portfolio performance."""
    return {
        'current_metrics': {
            'total_value': 100000,
            'total_return': 0.12,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.08
        },
        'performance': {
            'ytd_return': 0.15,
            '1y_return': 0.12,
            '3y_return': 0.18,
            '5y_return': 0.22
        }
    }

def calculate_portfolio_risk(portfolio: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate portfolio risk metrics."""
    return {
        'risk_metrics': {
            'portfolio_volatility': 0.15,
            'var_95': -0.05,
            'cvar_95': -0.07,
            'beta': 1.1
        },
        'correlation_matrix': {
            'AAPL': {'MSFT': 0.8, 'GOOGL': 0.7},
            'MSFT': {'AAPL': 0.8, 'GOOGL': 0.6},
            'GOOGL': {'AAPL': 0.7, 'MSFT': 0.6}
        }
    }

def optimize_portfolio_weights(portfolio: Dict[str, Any], risk_metrics: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize portfolio weights using modern portfolio theory."""
    return {
        'optimized_weights': {
            'AAPL': 0.30,
            'MSFT': 0.25,
            'GOOGL': 0.20,
            'Bonds': 0.25
        },
        'expected_return': 0.14,
        'expected_risk': 0.12
    }

def generate_rebalancing_plan(current_weights: Dict[str, Any], optimized_weights: Dict[str, Any]) -> Dict[str, Any]:
    """Generate rebalancing plan."""
    return {
        'rebalancing_plan': {
            'AAPL': {'current': 0.35, 'target': 0.30, 'action': 'SELL', 'amount': 0.05},
            'MSFT': {'current': 0.20, 'target': 0.25, 'action': 'BUY', 'amount': 0.05},
            'GOOGL': {'current': 0.25, 'target': 0.20, 'action': 'SELL', 'amount': 0.05},
            'Bonds': {'current': 0.20, 'target': 0.25, 'action': 'BUY', 'amount': 0.05}
        },
        'transaction_costs': 150.0
    }
```

## Usage Examples

```python
# Create a FinancialAnalyst
from core.agent import FinancialAnalyst

financial_analyst = FinancialAnalyst(llm_provider='anthropic', model='claude-3-sonnet')

# Use the agent
response = await financial_analyst.chat("Analyze AAPL stock and provide investment recommendation")

# The agent will:
# 1. Fetch market data for AAPL
# 2. Get company information and financials
# 3. Calculate technical and fundamental metrics
# 4. Analyze news sentiment
# 5. Generate comprehensive analysis and recommendation

# Example workflow execution
result = financial_analyst.execute_workflow('analyze_stock', {
    'symbol': 'AAPL',
    'period': '1y',
    'timeframe': '7d'
})

# Example portfolio optimization
portfolio_result = financial_analyst.execute_workflow('optimize_portfolio', {
    'portfolio': {
        'AAPL': 0.35,
        'MSFT': 0.25,
        'GOOGL': 0.20,
        'Bonds': 0.20
    },
    'benchmark': 'SPY',
    'constraints': {
        'max_weight': 0.40,
        'min_weight': 0.05,
        'rebalance_threshold': 0.05
    }
})

# Example resource usage
market_data = financial_analyst.query_resource('market_data', 'get_stock_data', {
    'symbol': 'AAPL',
    'period': '1y',
    'interval': '1d'
})

news_sentiment = financial_analyst.query_resource('financial_news', 'get_news', {
    'symbols': ['AAPL'],
    'limit': 10,
    'sentiment': True
})
```

## Configuration

```python
# FinancialAnalyst Configuration
financial_config = {
    'data_sources': ['yahoo', 'alpha_vantage', 'quandl'],
    'analysis_period': '1y',
    'confidence_threshold': 0.7,
    'risk_tolerance': 'moderate',
    'currency': 'USD',
    'timezone': 'UTC',
    'cache_duration': 3600,
    'max_portfolio_size': 50,
    'rebalance_frequency': 'monthly',
    'benchmark_index': 'SPY',
    'risk_free_rate': 0.02,
    'market_cap_threshold': 1000000000,
    'sector_analysis': True,
    'technical_indicators': True,
    'fundamental_analysis': True,
    'sentiment_analysis': True,
    'api_keys': {
        'alpha_vantage': 'your_alpha_vantage_key',
        'quandl': 'your_quandl_key'
    }
}
```

## Key Features

### 1. **Comprehensive Market Analysis**
- Real-time and historical market data
- Technical indicator calculations
- Market sentiment analysis
- Economic indicator tracking

### 2. **Portfolio Management**
- Portfolio optimization using modern portfolio theory
- Risk assessment and management
- Rebalancing recommendations
- Performance tracking

### 3. **Company Analysis**
- Financial statement analysis
- Fundamental metrics calculation
- Industry and sector analysis
- Competitive positioning

### 4. **News and Sentiment**
- Financial news aggregation
- Sentiment analysis
- Market sentiment tracking
- Event impact assessment

### 5. **Risk Management**
- Value at Risk (VaR) calculations
- Stress testing
- Correlation analysis
- Risk-adjusted returns

### 6. **Investment Research**
- Stock recommendations
- Sector analysis
- Market outlook
- Economic forecasting

This FinancialAnalyst implementation demonstrates how the agentic architecture can be specialized for financial domain tasks, providing comprehensive analysis capabilities while maintaining the flexibility and adaptability of the core system.

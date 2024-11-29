import logging

# Create and configure handler
handler = logging.StreamHandler()  # Outputs to terminal
handler.setLevel(logging.INFO)

# Modified formatter to include the extra fields
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
    'Details: %(messages)s\n'  # This will show the messages content
    'Response: %(response)s\n'  # This will show the response content
)
handler.setFormatter(formatter)

# Add handler to the root logger or specific logger
logger = logging.getLogger('dxa.llm')  # Gets all loggers under dxa.llm
logger.addHandler(handler)
logger.setLevel(logging.INFO) 
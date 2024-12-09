import logging

# Create and configure handler
handler = logging.StreamHandler()  # Outputs to terminal
handler.setLevel(logging.INFO)

# Modified formatter to handle missing custom fields gracefully
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
    'Details: %(messages)s\n'  # Will use empty string if messages is missing
    'Response: %(response)s\n',  # Will use empty string if response is missing
    defaults={
        'messages': '',
        'response': ''
    }
)
handler.setFormatter(formatter)

# Add handler to the root logger or specific logger
logger = logging.getLogger('dxa.llm')  # Gets all loggers under dxa.llm
logger.addHandler(handler)
logger.setLevel(logging.INFO) 
# Conditional Workflows

Dana provides powerful conditional workflow capabilities through the `case()` function, allowing you to build sophisticated decision trees and conditional logic in your programs. This primer covers how to effectively use conditional workflows in your Dana applications.

## Overview

The `case()` function enables pattern-matching style conditional logic, similar to switch statements in other languages but more flexible. It evaluates conditions in order and executes the first matching branch, with support for fallback values.

## Basic Syntax

```dana
result = case(
    (condition1, function1),
    (condition2, function2),
    fallback_function
)
```

## Simple Conditional Logic

### Basic Boolean Conditions

```dana
def handle_success():
    return "Operation completed successfully"

def handle_failure():
    return "Operation failed"

def process_result(success):
    return case(
        (success == true, handle_success),
        handle_failure  # fallback for any other case
    )

# Usage
result1 = process_result(true)   # "Operation completed successfully"
result2 = process_result(false)  # "Operation failed"
```

### Numeric Conditions

```dana
def handle_negative():
    return "Negative number"

def handle_zero():
    return "Zero value"

def handle_small():
    return "Small positive number"

def handle_large():
    return "Large number"

def classify_number(num):
    return case(
        (num < 0, handle_negative),
        (num == 0, handle_zero),
        (num <= 10, handle_small),
        handle_large
    )

# Usage
print(classify_number(-5))  # "Negative number"
print(classify_number(0))   # "Zero value"
print(classify_number(7))   # "Small positive number"
print(classify_number(50))  # "Large number"
```

## Advanced Patterns

### String Processing Workflows

```dana
def process_json_data(data):
    return f"Processing JSON: {data}"

def process_xml_data(data):
    return f"Processing XML: {data}"

def process_csv_data(data):
    return f"Processing CSV: {data}"

def process_unknown_data(data):
    return f"Unknown format: {data}"

def data_processor(data, format_type):
    return case(
        (format_type == "json", process_json_data),
        (format_type == "xml", process_xml_data),
        (format_type == "csv", process_csv_data),
        process_unknown_data
    )(data)

# Usage
result = data_processor("sample data", "json")
# "Processing JSON: sample data"
```

### Multi-Stage Workflows

```dana
def validate_input(data):
    if data:
        return data
    else:
        return "default_input"

def transform_for_development(data):
    return f"dev_transform: {data}"

def transform_for_production(data):
    return f"prod_transform: {data}"

def transform_for_testing(data):
    return f"test_transform: {data}"

def finalize_output(data):
    return f"final: {data}"

def is_development_environment():
    return true  # or check environment variables

def is_production_environment():
    return false  # or check environment variables

def complex_workflow(input_data, environment):
    # Step 1: Validate input
    validated = validate_input(input_data)
    
    # Step 2: Transform based on environment
    transform_func = case(
        (environment == "dev", transform_for_development),
        (environment == "prod", transform_for_production),
        (environment == "test", transform_for_testing),
        transform_for_development  # default to dev
    )
    transformed = transform_func(validated)
    
    # Step 3: Finalize
    return finalize_output(transformed)

# Usage
dev_result = complex_workflow("user_data", "dev")
prod_result = complex_workflow("user_data", "prod")
```

## Error Handling in Workflows

### Graceful Degradation

```dana
def primary_service():
    return "Primary service response"

def backup_service():
    return "Backup service response"

def emergency_fallback():
    return "Emergency fallback response"

def service_available():
    return true  # Check if primary service is available

def backup_available():
    return false  # Check if backup service is available

def resilient_workflow():
    return case(
        (service_available(), primary_service),
        (backup_available(), backup_service),
        emergency_fallback
    )

result = resilient_workflow()
```

### Validation Workflows

```dana
def validate_email(email):
    # Simple validation - in real code, use proper regex
    return "@" in email and "." in email

def validate_phone(phone):
    # Simple validation - in real code, use proper format checking
    return len(phone) >= 10

def send_email_notification(contact):
    return f"Email sent to: {contact}"

def send_sms_notification(contact):
    return f"SMS sent to: {contact}"

def log_notification_failure(contact):
    return f"Failed to notify: {contact}"

def notify_user(email, phone):
    return case(
        (validate_email(email), send_email_notification),
        (validate_phone(phone), send_sms_notification),
        log_notification_failure
    )(email or phone)

# Usage
result1 = notify_user("user@example.com", "")
result2 = notify_user("", "1234567890")
result3 = notify_user("invalid", "123")
```

## Integration with Functions and Agents

### Function Composition

```dana
def authenticate_user(credentials):
    return credentials == "valid_token"

def fetch_user_data(user_id):
    return f"User data for {user_id}"

def fetch_guest_data():
    return "Guest user data"

def format_response(data):
    return f"Response: {data}"

def secure_data_flow(credentials, user_id):
    # Authentication step
    auth_result = case(
        (authenticate_user(credentials), fetch_user_data),
        fetch_guest_data
    )
    
    # Data retrieval
    data = auth_result(user_id) if credentials == "valid_token" else auth_result()
    
    # Response formatting
    return format_response(data)

# Usage
authorized = secure_data_flow("valid_token", "user123")
unauthorized = secure_data_flow("invalid", "user123")
```

### Agent Decision Making

```dana
def route_to_support_agent():
    return "Routing to human support agent"

def route_to_sales_agent():
    return "Routing to sales agent"

def handle_with_chatbot():
    return "Handling with automated chatbot"

def analyze_intent(message):
    # In real implementation, this would use NLP
    if "help" in message or "support" in message:
        return "support"
    elif "buy" in message or "purchase" in message:
        return "sales"
    else:
        return "general"

def is_business_hours():
    return true  # Check current time

def customer_service_router(message):
    intent = analyze_intent(message)
    
    return case(
        (intent == "support" and is_business_hours(), route_to_support_agent),
        (intent == "sales" and is_business_hours(), route_to_sales_agent),
        handle_with_chatbot
    )

# Usage
response1 = customer_service_router("I need help with my account")
response2 = customer_service_router("I want to buy a product")
response3 = customer_service_router("What's the weather?")
```

## Performance Considerations

### Early Exit Patterns

The `case()` function evaluates conditions in order and stops at the first match, making it efficient for workflows where you want early exit behavior:

```dana
def expensive_check():
    # This won't be called if cheap_check() returns true
    return false

def cheap_check():
    return true

def fast_path():
    return "Fast execution path"

def slow_path():
    return "Slow execution path"

def optimized_workflow():
    return case(
        (cheap_check(), fast_path),      # Checked first
        (expensive_check(), slow_path),  # Only checked if needed
        fast_path                        # Fallback
    )
```

### Condition Ordering

Place the most likely or least expensive conditions first:

```dana
def common_case():
    return true

def rare_case():
    return false

def efficient_workflow():
    return case(
        (common_case(), "Common result"),  # Most likely - check first
        (rare_case(), "Rare result"),      # Less likely - check later
        "Default result"
    )
```

## Best Practices

### 1. Use Descriptive Function Names

```dana
# Good
def is_user_authenticated():
    return true

def handle_authenticated_request():
    return "Processing authenticated request"

def handle_unauthenticated_request():
    return "Please log in"

# Usage
response = case(
    (is_user_authenticated(), handle_authenticated_request),
    handle_unauthenticated_request
)
```

### 2. Keep Conditions Simple

```dana
# Good - simple, readable conditions
def process_user_level(level):
    return case(
        (level == "admin", handle_admin),
        (level == "user", handle_user),
        (level == "guest", handle_guest),
        handle_unknown_user
    )

# Avoid - complex conditions that are hard to read
def process_user_complex(user):
    return case(
        (user.level == "admin" and user.active and len(user.permissions) > 5, handle_admin),
        # ... other complex conditions
        handle_default
    )
```

### 3. Always Provide Fallbacks

```dana
# Good - always has a fallback
def safe_processor(input_type):
    return case(
        (input_type == "text", process_text),
        (input_type == "image", process_image),
        process_unknown  # Always provide fallback
    )

# Risky - could fail if no conditions match
def risky_processor(input_type):
    return case(
        (input_type == "text", process_text),
        (input_type == "image", process_image)
        # No fallback - could throw error
    )
```

### 4. Group Related Logic

```dana
# Data validation workflow
def validate_and_process(data):
    return case(
        (data == null, handle_null_data),
        (len(data) == 0, handle_empty_data),
        (len(data) > 1000, handle_large_data),
        process_normal_data
    )

# Authentication and authorization workflow  
def secure_operation(user, operation):
    return case(
        (not user.authenticated, request_authentication),
        (not user.authorized_for(operation), deny_access),
        (user.rate_limited, rate_limit_response),
        execute_operation
    )
```

## Common Patterns

### State Machines

```dana
def idle_state_handler():
    return "Handling idle state"

def running_state_handler():
    return "Handling running state"

def stopped_state_handler():
    return "Handling stopped state"

def error_state_handler():
    return "Handling error state"

def state_machine(current_state):
    return case(
        (current_state == "idle", idle_state_handler),
        (current_state == "running", running_state_handler),
        (current_state == "stopped", stopped_state_handler),
        (current_state == "error", error_state_handler),
        error_state_handler  # Default to error handling
    )
```

### Data Pipeline Routing

```dana
def csv_processor(data):
    return "Processing CSV data"

def json_processor(data):
    return "Processing JSON data"

def xml_processor(data):
    return "Processing XML data"

def unknown_processor(data):
    return "Processing unknown format"

def detect_format(data):
    # Simple format detection
    if data.startswith("{"):
        return "json"
    elif data.startswith("<"):
        return "xml"
    elif "," in data:
        return "csv"
    else:
        return "unknown"

def data_pipeline(raw_data):
    format = detect_format(raw_data)
    
    processor = case(
        (format == "csv", csv_processor),
        (format == "json", json_processor),
        (format == "xml", xml_processor),
        unknown_processor
    )
    
    return processor(raw_data)
```

## Debugging Workflows

### Adding Logging

```dana
def log_condition_check(condition_name, result):
    print(f"Condition '{condition_name}': {result}")
    return result

def debug_workflow(value):
    return case(
        (log_condition_check("is_positive", value > 0), handle_positive),
        (log_condition_check("is_zero", value == 0), handle_zero),
        handle_negative
    )
```

### Testing Workflows

```dana
def test_conditional_workflow():
    # Test positive case
    result1 = classify_number(5)
    assert result1 == "Small positive number"
    
    # Test negative case  
    result2 = classify_number(-3)
    assert result2 == "Negative number"
    
    # Test edge case
    result3 = classify_number(0)
    assert result3 == "Zero value"
    
    # Test fallback
    result4 = classify_number(100)
    assert result4 == "Large number"
    
    print("All tests passed!")

test_conditional_workflow()
```

## Conclusion

The `case()` function provides a powerful and readable way to implement conditional workflows in Dana. By following the patterns and best practices outlined in this primer, you can create maintainable, efficient, and robust conditional logic in your applications.

Key takeaways:

- Use `case()` for clean, readable conditional logic
- Always provide fallback values
- Order conditions by likelihood or cost
- Keep individual conditions simple and descriptive
- Test all branches of your conditional workflows
- Use conditional workflows to implement state machines, data pipelines, and decision trees

For more advanced patterns and examples, see the Dana documentation and explore the test cases in the Dana codebase.
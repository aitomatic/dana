# Dana Structs and Methods - Complete User Guide

*A comprehensive guide to using Dana's struct system for building robust, maintainable code*

---

## Table of Contents

1. [Quick Start with Structs](#quick-start-with-structs)
2. [Dana vs Python vs Go](#dana-vs-python-vs-go)
3. [Struct Fundamentals](#struct-fundamentals)
4. [Method System](#method-system)
5. [Advanced Patterns](#advanced-patterns)
6. [Best Practices](#best-practices)
7. [Common Pitfalls](#common-pitfalls)
8. [Real-World Examples](#real-world-examples)

---

## Quick Start with Structs

### Your First Struct

```dana
# Define a struct
struct User:
    name: str
    email: str
    age: int

# Create instances
user = User(name="Alice", email="alice@example.com", age=30)

# Access fields
print(f"User: {user.name} ({user.email})")
user.age = 31  # Structs are mutable
```

### Your First Method

```dana
# Define a function that operates on the struct
def greet(user: User) -> str:
    return f"Hello, {user.name}!"

# Call it as a method using syntactic sugar
greeting = user.greet()  # Equivalent to greet(user)
print(greeting)  # "Hello, Alice!"
```

---

## Dana vs Python vs Go

Understanding Dana's design helps you write better code by leveraging its unique strengths.

### The Philosophy

| Language | Data + Behavior | Type System | AI Integration |
|----------|----------------|-------------|----------------|
| **Python** | Classes combine data and methods | Dynamic typing | Limited |
| **Go** | Structs for data, functions for behavior | Static typing | None |
| **Dana** | Structs for data, functions for behavior | Dynamic typing with hints | Native AI reasoning |

### Code Comparison

#### Python Approach
```python
class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance
    
    def deposit(self, amount: float) -> float:
        self.balance += amount
        return self.balance
    
    def withdraw(self, amount: float) -> float:
        if amount <= self.balance:
            self.balance -= amount
        return self.balance

# Usage
account = BankAccount(100.0)
account.deposit(50.0)
```

#### Go Approach
```go
type BankAccount struct {
    Balance float64
}

func (a *BankAccount) Deposit(amount float64) float64 {
    a.Balance += amount
    return a.Balance
}

func (a *BankAccount) Withdraw(amount float64) float64 {
    if amount <= a.Balance {
        a.Balance -= amount
    }
    return a.Balance
}

// Usage
account := BankAccount{Balance: 100.0}
account.Deposit(50.0)
```

#### Dana Approach
```dana
struct BankAccount:
    balance: float

def deposit(account: BankAccount, amount: float) -> float:
    account.balance = account.balance + amount
    return account.balance

def withdraw(account: BankAccount, amount: float) -> float:
    if amount <= account.balance:
        account.balance = account.balance - amount
    return account.balance

# Usage - looks like Python, works like Go
account = BankAccount(balance=100.0)
new_balance = account.deposit(50.0)  # Method syntax sugar
```

### Why Dana's Approach Matters

1. **AI-Friendly**: Functions can be easily discovered and called by AI agents
2. **Polymorphic**: Same function name works with different struct types
3. **Flexible**: Dynamic typing adapts to changing requirements
4. **Functional**: Encourages functional programming patterns

---

## Struct Fundamentals

### Defining Structs

```dana
# Basic struct
struct Point:
    x: int
    y: int

# Complex struct with various types
struct Customer:
    id: str
    name: str
    email: str
    age: int
    active: bool
    tags: list
    metadata: dict
    address: Address  # Another struct
```

### Type Hints - Your AI Assistant's Best Friend

Dana's type hints serve multiple purposes:

```dana
struct Product:
    id: str          # AI knows this should be a string
    price: float     # AI can help with price calculations
    in_stock: bool   # AI understands boolean logic
    categories: list # AI knows this is a collection

# Type hints help AI generate better code
def calculate_discount(product: Product, percentage: float) -> float:
    # AI understands the types and can suggest appropriate operations
    return product.price * (1.0 - percentage / 100.0)
```

### Instantiation Patterns

```dana
# Explicit named arguments (recommended)
user = User(
    name="John Doe",
    email="john@example.com", 
    age=25
)

# With complex nested data
order = Order(
    id="ORD-001",
    customer=user,
    items=[
        OrderItem(product_id="PROD-123", quantity=2, price=29.99),
        OrderItem(product_id="PROD-456", quantity=1, price=49.99)
    ],
    total=109.97
)
```

### Field Access and Mutation

```dana
# Direct field access
customer_name = user.name
user.email = "newemail@example.com"

# Chained access (now supported!)
first_item_price = order.items[0].price
customer_city = order.customer.address.city

# Safe access patterns
if order.items and len(order.items) > 0:
    first_item = order.items[0]
    log(f"First item: {first_item.product_id}")
```

---

## Method System

### The Magic of Method Syntax Sugar

Dana transforms `obj.method()` calls into `method(obj)` function calls at runtime.

```dana
struct Document:
    content: str
    title: str

def analyze(doc: Document) -> str:
    # AI can analyze the document content
    return reason("Analyze this document for key themes", context=doc.content)

def summarize(doc: Document, max_length: int = 100) -> str:
    summary = reason(f"Summarize in {max_length} words", context=doc.content)
    return summary

# These are equivalent:
doc = Document(content="...", title="Report")
analysis1 = doc.analyze()           # Method syntax
analysis2 = analyze(doc)            # Function syntax

summary1 = doc.summarize(50)        # Method with args
summary2 = summarize(doc, 50)       # Function with args
```

### Polymorphism - One Function, Multiple Types

```dana
struct TextDocument:
    content: str

struct ImageDocument:
    image_data: str
    alt_text: str

# Same function name, different types
def analyze(doc: TextDocument) -> str:
    return reason("Analyze text content", context=doc.content)

def analyze(img: ImageDocument) -> str:
    return reason("Analyze image content", context=[img.image_data, img.alt_text])

# Runtime dispatch based on type
text_doc = TextDocument(content="Important report...")
image_doc = ImageDocument(image_data="...", alt_text="Chart showing trends")

text_analysis = text_doc.analyze()    # Calls text version
image_analysis = image_doc.analyze()  # Calls image version
```

### Function Signature Requirements

**Critical Rule**: For struct methods, the struct type must be the first named parameter.

```dana
# ✅ Correct signatures
def process(user: User, action: str) -> bool:
    return True

def transform(data: Dataset, *filters: str, **options: dict) -> Dataset:
    return data

def validate(config: Config, strict: bool = True) -> bool:
    return True

# ❌ Incorrect signatures  
def process(action: str, user: User) -> bool:     # Struct not first
    return True

def transform(*args, data: Dataset) -> Dataset:   # Struct not first named param
    return data
```

### Method Chaining

```dana
struct Calculator:
    value: float

def add(calc: Calculator, x: float) -> Calculator:
    calc.value = calc.value + x
    return calc

def multiply(calc: Calculator, x: float) -> Calculator:
    calc.value = calc.value * x
    return calc

def get_result(calc: Calculator) -> float:
    return calc.value

# Method chaining
result = Calculator(value=10.0).add(5).multiply(2).get_result()
# result = 30.0
```

---

## Advanced Patterns

### Complex Data Hierarchies

```dana
struct Address:
    street: str
    city: str
    country: str
    postal_code: str

struct Company:
    name: str
    address: Address
    employees: list

struct Employee:
    name: str
    email: str
    company: Company
    role: str

def get_company_city(employee: Employee) -> str:
    return employee.company.address.city

def format_employee_info(emp: Employee) -> str:
    return f"{emp.name} ({emp.role}) at {emp.company.name}"

# Usage with deep nesting
company = Company(
    name="Tech Corp",
    address=Address(
        street="123 Innovation Dr",
        city="San Francisco", 
        country="USA",
        postal_code="94105"
    ),
    employees=[]
)

employee = Employee(
    name="Alice Johnson",
    email="alice@techcorp.com", 
    company=company,
    role="Senior Engineer"
)

# Complex field access
city = employee.get_company_city()
info = employee.format_employee_info()
```

### Working with Collections

```dana
struct OrderItem:
    product_id: str
    quantity: int
    unit_price: float

struct Order:
    id: str
    items: list
    status: str

def add_item(order: Order, product_id: str, quantity: int, price: float) -> Order:
    new_item = OrderItem(
        product_id=product_id,
        quantity=quantity, 
        unit_price=price
    )
    order.items.append(new_item)
    return order

def calculate_total(order: Order) -> float:
    total = 0.0
    for item in order.items:
        total = total + (item.quantity * item.unit_price)
    return total

def get_expensive_items(order: Order, threshold: float) -> list:
    expensive = []
    for item in order.items:
        if item.unit_price > threshold:
            expensive.append(item)
    return expensive

# Usage
order = Order(id="ORD-001", items=[], status="pending")
order = order.add_item("PROD-123", 2, 29.99)
order = order.add_item("PROD-456", 1, 99.99)

total = order.calculate_total()
expensive = order.get_expensive_items(50.0)
```

### AI Integration Patterns

```dana
struct DataSet:
    data: list
    source: str
    timestamp: str

def analyze_trends(dataset: DataSet) -> str:
    # Let AI analyze the data
    analysis = reason(
        "Analyze this dataset for trends and patterns",
        context=dataset.data
    )
    return analysis

def generate_insights(dataset: DataSet, focus_area: str) -> str:
    # AI-powered insights with context
    insights = reason(
        f"Generate insights about {focus_area}",
        context=[dataset.data, dataset.source]
    )
    return insights

def predict_outcomes(dataset: DataSet, scenario: str) -> str:
    # AI predictions
    prediction = reason(
        f"Based on this data, predict outcomes for: {scenario}",
        context=dataset.data,
        temperature=0.7  # Slightly creative
    )
    return prediction

# AI-powered data analysis
sales_data = DataSet(
    data=[{"month": "Jan", "sales": 10000}, {"month": "Feb", "sales": 12000}],
    source="sales_system",
    timestamp="2024-01-15"
)

trends = sales_data.analyze_trends()
insights = sales_data.generate_insights("seasonal patterns")
forecast = sales_data.predict_outcomes("Q2 sales targets")
```

---

## Best Practices

### 1. Design for Clarity

```dana
# ✅ Good: Clear, descriptive field names
struct CustomerProfile:
    customer_id: str
    full_name: str
    email_address: str
    registration_date: str
    subscription_tier: str
    is_active: bool

# ❌ Avoid: Cryptic or unclear names
struct Customer:
    id: str
    n: str
    e: str
    rd: str
    st: str
    a: bool
```

### 2. Embrace Type Hints

```dana
# ✅ Good: Comprehensive type hints help AI assistance
def process_order(order: Order, payment_method: str, discount_code: str = None) -> bool:
    # AI can understand the expected types and suggest appropriate operations
    if discount_code:
        apply_discount(order, discount_code)
    return process_payment(order, payment_method)

# ❌ Avoid: Missing type hints make AI assistance less effective
def process_order(order, payment_method, discount_code = None):
    # AI has to guess types and operations
    pass
```

### 3. Function Naming for Polymorphism

```dana
# ✅ Good: Same logical operation, different implementations
def validate(user: User) -> bool:
    return user.email and "@" in user.email

def validate(order: Order) -> bool:
    return len(order.items) > 0 and order.total > 0

def validate(payment: Payment) -> bool:
    return payment.amount > 0 and payment.method in ["card", "bank"]

# Users can call .validate() on any object
```

### 4. Leverage AI Reasoning

```dana
struct SupportTicket:
    id: str
    customer_id: str
    subject: str
    description: str
    priority: str
    status: str

def analyze_sentiment(ticket: SupportTicket) -> str:
    # Let AI determine customer sentiment
    sentiment = reason(
        "Analyze the sentiment of this support ticket",
        context=[ticket.subject, ticket.description]
    )
    return sentiment

def suggest_priority(ticket: SupportTicket) -> str:
    # AI-driven priority suggestion
    priority = reason(
        "Suggest an appropriate priority level for this ticket",
        context=[ticket.subject, ticket.description],
        format="one_word"  # Just return: low, medium, high, urgent
    )
    return priority

def generate_response(ticket: SupportTicket) -> str:
    # AI-generated response template
    response = reason(
        "Generate a professional response template for this support ticket",
        context=[ticket.subject, ticket.description]
    )
    return response
```

### 5. Error Handling and Validation

```dana
struct BankAccount:
    account_number: str
    balance: float
    account_type: str

def withdraw(account: BankAccount, amount: float) -> bool:
    # Validate inputs
    if amount <= 0:
        log("Invalid withdrawal amount", level="error")
        return false
    
    if amount > account.balance:
        log(f"Insufficient funds: requested {amount}, available {account.balance}", level="warn")
        return false
    
    # Perform withdrawal
    account.balance = account.balance - amount
    log(f"Withdrawal successful: {amount}, new balance: {account.balance}")
    return true

def transfer(from_account: BankAccount, to_account: BankAccount, amount: float) -> bool:
    # Validate accounts exist
    if not from_account or not to_account:
        log("Invalid account for transfer", level="error")
        return false
    
    # Perform transfer
    if from_account.withdraw(amount):
        to_account.balance = to_account.balance + amount
        log(f"Transfer completed: {amount} from {from_account.account_number} to {to_account.account_number}")
        return true
    
    return false
```

---

## Common Pitfalls

### 1. Function Overloading Limitation (Current)

```dana
# ❌ Currently not supported - second function overwrites first
def process(user: User) -> str:
    return "Processing user"

def process(user: User) -> str:  # This overwrites the first one
    return "Different processing"

# ✅ Current workaround - use descriptive names
def process_basic(user: User) -> str:
    return "Processing user"

def process_advanced(user: User) -> str:
    return "Advanced processing"
```

### 2. Chained Access Errors

```dana
# ✅ Safe chained access
struct Company:
    address: Address

struct Address:
    city: str

# Check for existence before accessing
company = Company(address=Address(city="San Francisco"))
if company.address:
    city = company.address.city

# Or use defensive programming
def get_company_city(company: Company) -> str:
    if company and company.address and company.address.city:
        return company.address.city
    return "Unknown"
```

### 3. Type Coercion Issues

```dana
struct Point:
    x: int
    y: int

def calculate_midpoint(p1: Point, p2: Point) -> Point:
    # ✅ Ensure integer results
    mid_x = int((p1.x + p2.x) / 2)
    mid_y = int((p1.y + p2.y) / 2)
    return Point(x=mid_x, y=mid_y)
    
    # ❌ Avoid - may result in type mismatch
    # mid_x = (p1.x + p2.x) // 2  # Could return float
```

---

## Real-World Examples

### E-commerce System

```dana
struct Product:
    id: str
    name: str
    price: float
    category: str
    in_stock: bool

struct CartItem:
    product: Product
    quantity: int

struct ShoppingCart:
    customer_id: str
    items: list
    discount_code: str

def add_to_cart(cart: ShoppingCart, product: Product, quantity: int) -> ShoppingCart:
    # Check stock
    if not product.in_stock:
        log(f"Product {product.name} is out of stock", level="warn")
        return cart
    
    # Check if item already in cart
    existing_item = None
    for item in cart.items:
        if item.product.id == product.id:
            existing_item = item
            break
    
    if existing_item:
        existing_item.quantity = existing_item.quantity + quantity
        log(f"Updated quantity for {product.name}: {existing_item.quantity}")
    else:
        new_item = CartItem(product=product, quantity=quantity)
        cart.items.append(new_item)
        log(f"Added {product.name} to cart: {quantity}")
    
    return cart

def calculate_total(cart: ShoppingCart) -> float:
    subtotal = 0.0
    for item in cart.items:
        subtotal = subtotal + (item.product.price * item.quantity)
    
    # Apply discount
    if cart.discount_code:
        discount = calculate_discount(subtotal, cart.discount_code)
        subtotal = subtotal - discount
    
    return subtotal

def recommend_products(cart: ShoppingCart) -> list:
    # AI-powered recommendations
    categories = []
    for item in cart.items:
        if item.product.category not in categories:
            categories.append(item.product.category)
    
    recommendations = reason(
        "Recommend products based on cart contents",
        context=categories
    )
    return recommendations

# Usage
cart = ShoppingCart(customer_id="CUST-001", items=[], discount_code=None)
product = Product(id="PROD-123", name="Laptop", price=999.99, category="Electronics", in_stock=true)

cart = cart.add_to_cart(product, 1)
total = cart.calculate_total()
suggestions = cart.recommend_products()
```

### Document Processing System

```dana
struct Document:
    id: str
    title: str
    content: str
    doc_type: str
    created_at: str
    tags: list

struct ProcessingResult:
    document_id: str
    summary: str
    key_points: list
    sentiment: str
    confidence: float

def extract_key_points(doc: Document) -> list:
    # AI extraction
    points = reason(
        "Extract the top 5 key points from this document",
        context=doc.content,
        format="list"
    )
    return points

def analyze_sentiment(doc: Document) -> str:
    # AI sentiment analysis
    sentiment = reason(
        "What is the overall sentiment of this document?",
        context=doc.content,
        format="one_word"  # positive, negative, neutral
    )
    return sentiment

def generate_summary(doc: Document, max_words: int = 100) -> str:
    # AI summarization
    summary = reason(
        f"Summarize this document in {max_words} words or less",
        context=doc.content
    )
    return summary

def process_document(doc: Document) -> ProcessingResult:
    # Comprehensive processing
    log(f"Processing document: {doc.title}")
    
    summary = doc.generate_summary()
    key_points = doc.extract_key_points()
    sentiment = doc.analyze_sentiment()
    
    # Calculate confidence based on content length and clarity
    confidence = calculate_confidence(doc)
    
    result = ProcessingResult(
        document_id=doc.id,
        summary=summary,
        key_points=key_points,
        sentiment=sentiment,
        confidence=confidence
    )
    
    log(f"Processing complete for {doc.title}: {sentiment} sentiment, {confidence:.2f} confidence")
    return result

def calculate_confidence(doc: Document) -> float:
    # Simple confidence calculation based on content characteristics
    content_length = len(doc.content)
    if content_length < 100:
        return 0.5
    elif content_length < 1000:
        return 0.7
    else:
        return 0.9

# Usage
document = Document(
    id="DOC-001",
    title="Q4 Sales Report",
    content="This quarter has shown remarkable growth...",
    doc_type="report",
    created_at="2024-01-15",
    tags=["sales", "quarterly", "analysis"]
)

result = document.process_document()
print(f"Summary: {result.summary}")
print(f"Sentiment: {result.sentiment}")
print(f"Key points: {len(result.key_points)}")
```

---

## Performance Considerations

While Dana prioritizes developer experience and AI integration over raw performance, understanding the current characteristics helps you write efficient code:

### Current Benchmarks

- **Struct Creation**: ~0.7x compared to Python dicts (actually faster!)
- **Method Calls**: ~4x overhead compared to direct function calls
- **Field Access**: ~9x overhead compared to Python dict access

### Optimization Tips

```dana
# ✅ For high-frequency operations, consider direct function calls
def hot_path_calculation(data: DataSet) -> float:
    # Direct function call for performance-critical code
    return calculate_statistics(data)

# ✅ Batch operations when possible
def process_multiple_orders(orders: list) -> list:
    results = []
    for order in orders:
        result = order.calculate_total()  # Method call is fine here
        results.append(result)
    return results

# ✅ Cache expensive AI operations
processed_cache = {}

def expensive_analysis(doc: Document) -> str:
    if doc.id in processed_cache:
        return processed_cache[doc.id]
    
    analysis = reason("Deep analysis of document", context=doc.content)
    processed_cache[doc.id] = analysis
    return analysis
```

---

## Migration from Other Languages

### From Python Classes

```python
# Python class
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    
    def greet(self) -> str:
        return f"Hello, {self.name}!"
```

```dana
# Dana equivalent
struct User:
    name: str
    email: str

def greet(user: User) -> str:
    return f"Hello, {user.name}!"

# Usage is nearly identical
user = User(name="Alice", email="alice@example.com")
greeting = user.greet()
```

### From Go Structs

```go
// Go struct and method
type User struct {
    Name  string
    Email string
}

func (u User) Greet() string {
    return fmt.Sprintf("Hello, %s!", u.Name)
}
```

```dana
# Dana equivalent  
struct User:
    name: str
    email: str

def greet(user: User) -> str:
    return f"Hello, {user.name}!"
```

---

## Summary

Dana's struct system combines the best of both worlds:

- **Python-like syntax**: Familiar and readable
- **Go-like separation**: Data and behavior are separate
- **AI-first design**: Built for reasoning and automation
- **Dynamic flexibility**: Adapts to changing requirements

Key takeaways:

1. **Structs hold data**, **functions define behavior**
2. **Method syntax sugar** makes code readable while maintaining functional principles  
3. **Type hints** are your friend - they help both AI and humans understand your code
4. **Polymorphism** through function dispatch enables flexible, reusable code
5. **AI integration** is natural and powerful when combined with well-structured data

Start with simple structs and functions, then gradually adopt more advanced patterns as your applications grow in complexity.

---

## Next Steps

- Explore [Real-World Recipes](../recipes/README.md) for more complex examples
- Learn about [API Integration Patterns](../recipes/api-integration/README.md)
- Explore more [Dana Reference Documentation](../reference/README.md)
- See [Troubleshooting Guide](../troubleshooting/README.md) for common issues

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
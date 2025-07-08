#!/usr/bin/env python3
"""
Example 2: Enterprise System Enhancement - Zero Risk AI Addition

Demonstrates adding AI capabilities to mission-critical production systems
without changing ANY existing business logic.

Key Insight: AI enhancement, not replacement!
"""

import logging

from opendxa.dana import dana

# Hide all INFO logs system-wide
logging.getLogger().setLevel(logging.WARNING)


class ProductionOrderSystem:
    """
    EXISTING PRODUCTION SYSTEM (DO NOT CHANGE!)
    
    This represents your existing enterprise system with millions in revenue.
    """
    
    def __init__(self):
        self.orders_processed = 0
        
    def process_order(self, order_data):
        """EXISTING: Your battle-tested order processing logic"""
        print(f"\n\033[1;36m📦 Processing order #{order_data['order_id']}\033[0m")
        
        # EXISTING: All your current business logic (unchanged)
        self.validate_payment(order_data)
        self.check_inventory(order_data)
        self.calculate_shipping(order_data)
        self.update_database(order_data)
        
        # NEW: ADD AI SUPERPOWERS USING DANA MODULES (ZERO RISK!)
        print("\n\033[1;35m  🤖 Adding AI insights...\033[0m")
        dana.enable_module_imports()
        try:
            import order_intelligence  # Dana module for organized AI logic
            
            ai_analysis = order_intelligence.analyze_order(order_data)
            
            # Store AI insights (doesn't affect existing flow)
            order_data['ai_insights'] = ai_analysis
            print(f"\033[38;5;147m  💡 AI Insights: {ai_analysis}\033[0m")
            
        finally:
            dana.disable_module_imports()
        
        # EXISTING: Continue with your normal flow (unchanged)
        self.send_confirmation_email(order_data)
        self.orders_processed += 1
        
        return order_data
    
    # EXISTING METHODS (all unchanged)
    def validate_payment(self, order_data):
        print("\033[32m  💳 Payment validated\033[0m")
        
    def check_inventory(self, order_data):
        print("\033[32m  📦 Inventory checked\033[0m")
        
    def calculate_shipping(self, order_data):
        print("\033[32m  🚚 Shipping calculated\033[0m")
        
    def update_database(self, order_data):
        print("\033[32m  💾 Database updated\033[0m")
        
    def send_confirmation_email(self, order_data):
        print("\033[32m  📧 Confirmation email sent\033[0m")


def main():
    print("\n\033[1;36m🎯 Example 2: Enterprise System Enhancement\033[0m")
    print("\033[38;5;147m" + "=" * 50 + "\033[0m")
    
    print("\033[1;34m🏭 Your existing production system (DO NOT CHANGE)\033[0m")
    system = ProductionOrderSystem()
    
    # Sample order (like your real production data)
    sample_order = {
        "order_id": "ORD_12345",
        "customer_tier": "Premium",
        "customer_history": 15,
        "amount": 2500.00,
        "items": 3,
        "shipping_country": "USA"
    }
    
    print("\n\033[1;33m🔄 Processing order with AI enhancement...\033[0m")
    enhanced_order = system.process_order(sample_order)
    
    print("\n\033[1;32m✅ Order processed successfully!\033[0m")
    print(f"\033[38;5;147m📊 Orders processed: {system.orders_processed}\033[0m")
    print(f"\033[38;5;147m🤖 AI enhancement: {'Added' if 'ai_insights' in enhanced_order else 'Failed'}\033[0m")
    
    print("\n\033[1;36m💡 RESULT:\033[0m")
    print("\033[32m  ✅ Zero changes to existing business logic\033[0m")
    print("\033[32m  ✅ AI logic organized in reusable Dana modules\033[0m") 
    print("\033[32m  ✅ Easy to add more AI capabilities\033[0m")
    print("\033[32m  ✅ Team can collaborate on AI modules\033[0m\n")


if __name__ == "__main__":
    main() 
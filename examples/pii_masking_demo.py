"""Example demonstrating PII masking in structlog for Eagle Bank API."""

import structlog
from app.core.logging_processors import mask_pii_processor, compliance_processor, security_processor


def setup_example_logger():
    """Setup structlog with PII masking for demonstration."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_pii_processor,                      # Mask PII
            compliance_processor,                    # Add compliance metadata
            security_processor,                      # Add security alerts
            structlog.processors.JSONRenderer()     # Output as JSON
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger(__name__)


def demonstrate_pii_masking():
    """Demonstrate PII masking in various banking scenarios."""
    
    logger = setup_example_logger()
    
    print("🔒 Eagle Bank API - PII Masking Demonstration")
    print("=" * 60)
    
    # Example 1: User Registration
    print("\n📝 1. User Registration (Sensitive Data Masked):")
    logger.info(
        "User registration completed",
        user_id="user_12345",
        email="john.doe@example.com",           # Will be masked
        phone_number="+447700900123",           # Will be masked  
        account_number="12345678",              # Will be masked
        initial_balance=1000.00,                # Safe to log
        account_type="savings",                 # Safe to log
        registration_ip="192.168.1.100"        # Will be masked
    )
    
    # Example 2: Transaction Processing
    print("\n💳 2. Transaction Processing:")
    logger.info(
        "Transaction processed successfully",
        transaction_id="tx_789456",
        account_number="87654321",              # Will be masked
        amount=250.00,                          # Safe to log
        currency="GBP",                         # Safe to log
        transaction_type="deposit",             # Safe to log
        user_email="alice.smith@bank.com",     # Will be masked
        processing_time_ms=145                  # Safe to log
    )
    
    # Example 3: Authentication Event
    print("\n🔐 3. Authentication Event:")
    logger.warning(
        "Multiple failed login attempts detected",
        user_email="suspicious@hacker.com",     # Will be masked
        ip_address="10.0.0.1",                 # Will be masked
        attempt_count=5,                        # Safe to log
        time_window_minutes=10,                 # Safe to log
        user_agent="Mozilla/5.0...",           # Safe to log
        password="secret123"                    # Will be fully masked
    )
    
    # Example 4: Account Balance Inquiry
    print("\n💰 4. Account Balance Inquiry:")
    logger.info(
        "Account balance checked",
        account_number="11223344",              # Will be masked
        current_balance=5420.75,                # Safe to log
        user_id="user_98765",                   # Safe to log
        client_ip="203.0.113.45",              # Will be masked
        access_token="eyJhbGciOiJIUzI1NiIs...", # Will be fully masked
        request_timestamp="2025-08-06T10:30:15Z" # Safe to log
    )
    
    # Example 5: Card Transaction
    print("\n💳 5. Card Transaction:")
    logger.info(
        "Card payment processed",
        card_number="4532123456789012",         # Will be masked
        cvv="123",                              # Will be fully masked
        cardholder_email="customer@shop.com",  # Will be masked
        merchant_id="merchant_456",             # Safe to log
        amount=89.99,                           # Safe to log
        currency="GBP",                         # Safe to log
        authorization_code="AUTH123"            # Safe to log
    )
    
    # Example 6: Compliance and Audit
    print("\n📋 6. Compliance and Audit Event:")
    logger.info(
        "Regulatory report generated",
        report_type="suspicious_activity",      # Safe to log
        account_numbers=["12345678", "87654321"], # Will be masked
        date_range="2025-08-01 to 2025-08-06", # Safe to log
        total_transactions=1247,                # Safe to log
        flagged_transactions=3,                 # Safe to log
        compliance_officer="officer_123"        # Safe to log
    )
    
    # Example 7: System Security Event
    print("\n🚨 7. Security Alert:")
    logger.error(
        "Potential fraud detected",
        alert_type="unusual_transaction_pattern",
        account_number="99887766",              # Will be masked
        user_email="victim@example.com",       # Will be masked
        transaction_amounts=[100, 200, 500, 1000], # Safe to log
        risk_score=85,                          # Safe to log
        automated_action="account_frozen",      # Safe to log
        investigation_required=True             # Safe to log
    )


def demonstrate_masking_levels():
    """Show different levels of masking for different data types."""
    
    logger = setup_example_logger()
    
    print("\n🎭 PII Masking Levels Demonstration")
    print("-" * 40)
    
    # Test different email formats
    emails = [
        "short@ex.com",
        "john.doe@example.com", 
        "very.long.email.address@corporation.co.uk"
    ]
    
    for email in emails:
        logger.info("Email test", original_email=email, email=email)
    
    # Test different phone formats
    phones = [
        "+447700900123",
        "07700 900 123", 
        "+1-555-123-4567",
        "123-456-7890"
    ]
    
    for phone in phones:
        logger.info("Phone test", original_phone=phone, phone_number=phone)
    
    # Test account numbers
    account_numbers = [
        "12345678",
        "GB29 NWBK 6016 1331 9268 19",
        "4532 1234 5678 9012"
    ]
    
    for account in account_numbers:
        logger.info("Account test", original_account=account, account_number=account)


if __name__ == "__main__":
    # Run the demonstrations
    demonstrate_pii_masking()
    demonstrate_masking_levels()
    
    print("\n" + "=" * 60)
    print("🔒 All sensitive data has been automatically masked!")
    print("✅ Logs are now safe for:")
    print("  • Development and debugging")
    print("  • Log aggregation systems") 
    print("  • Compliance audits")
    print("  • Security analysis")
    print("  • Performance monitoring")

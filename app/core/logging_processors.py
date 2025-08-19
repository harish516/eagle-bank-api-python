"""Custom structlog processors for PII masking and security."""

import re
from typing import Any, Dict, List, Union
import structlog


# Sensitive fields that should be masked
SENSITIVE_FIELDS = {
    # Personal Information
    'email', 'email_address', 'user_email',
    'phone', 'phone_number', 'mobile',
    'ssn', 'social_security_number',
    'passport', 'passport_number',
    'license', 'driving_license',
    
    # Financial Information
    'account_number', 'card_number', 'credit_card',
    'bank_account', 'iban', 'routing_number',
    'cvv', 'pin', 'security_code',
    
    # Authentication
    'password', 'token', 'secret', 'api_key',
    'access_token', 'refresh_token', 'jwt',
    
    # Addresses (partial masking)
    'address', 'street_address', 'home_address',
    'ip_address', 'client_ip'
}

# Fields that need partial masking (show first/last few characters)
PARTIAL_MASK_FIELDS = {
    'email', 'email_address', 'user_email',
    'phone', 'phone_number', 'mobile',
    'account_number', 'card_number',
    'ip_address', 'client_ip'
}


def mask_email(email: str) -> str:
    """Mask email address: john.doe@example.com -> j***@ex***"""
    if '@' not in email:
        return "***"
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    
    if '.' in domain:
        domain_parts = domain.split('.')
        masked_domain = domain_parts[0][:2] + "*" * (len(domain_parts[0]) - 2) + "." + domain_parts[-1]
    else:
        masked_domain = domain[:2] + "*" * (len(domain) - 2)
    
    return f"{masked_local}@{masked_domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number: +447700900123 -> +44***123"""
    # Remove all non-digit characters except +
    clean_phone = re.sub(r'[^\d+]', '', str(phone))
    
    if len(clean_phone) < 4:
        return "*" * len(clean_phone)
    
    if clean_phone.startswith('+'):
        return clean_phone[:3] + "*" * (len(clean_phone) - 6) + clean_phone[-3:]
    else:
        return clean_phone[:2] + "*" * (len(clean_phone) - 5) + clean_phone[-3:]


def mask_account_number(account_num: str) -> str:
    """Mask account number: 12345678 -> 12***78"""
    account_str = str(account_num)
    if len(account_str) <= 4:
        return "*" * len(account_str)
    
    return account_str[:2] + "*" * (len(account_str) - 4) + account_str[-2:]


def mask_ip_address(ip: str) -> str:
    """Mask IP address: 192.168.1.100 -> 192.168.***.***"""
    if '.' in ip:  # IPv4
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.***.**"
    elif ':' in ip:  # IPv6
        parts = ip.split(':')
        if len(parts) >= 4:
            return f"{parts[0]}:{parts[1]}:***:***"
    
    return "***"


def mask_sensitive_value(key: str, value: Any) -> str:
    """Apply appropriate masking based on field type."""
    value_str = str(value)
    
    if not value_str or value_str.lower() in ['none', 'null', '']:
        return value_str
    
    key_lower = key.lower()
    
    # Full masking for highly sensitive fields
    if any(sensitive in key_lower for sensitive in ['password', 'secret', 'token', 'cvv', 'pin', 'ssn']):
        return "***"
    
    # Partial masking for identifiable but loggable fields
    if 'email' in key_lower:
        return mask_email(value_str)
    elif 'phone' in key_lower or 'mobile' in key_lower:
        return mask_phone(value_str)
    elif 'account' in key_lower and 'number' in key_lower:
        return mask_account_number(value_str)
    elif 'ip' in key_lower and 'address' in key_lower:
        return mask_ip_address(value_str)
    elif any(field in key_lower for field in ['card_number', 'credit_card']):
        return mask_account_number(value_str)
    
    # Default partial masking
    if len(value_str) <= 3:
        return "*" * len(value_str)
    else:
        return value_str[:1] + "*" * (len(value_str) - 2) + value_str[-1:]


def mask_pii_processor(logger, method_name, event_dict):
    """Structlog processor to mask PII in log events."""
    
    def mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask sensitive data in dictionaries."""
        masked_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if this field should be masked
            if any(sensitive_field in key_lower for sensitive_field in SENSITIVE_FIELDS):
                if key_lower in PARTIAL_MASK_FIELDS or any(partial in key_lower for partial in PARTIAL_MASK_FIELDS):
                    masked_data[key] = mask_sensitive_value(key, value)
                else:
                    masked_data[key] = "***"
            elif isinstance(value, dict):
                masked_data[key] = mask_dict(value)
            elif isinstance(value, list):
                masked_data[key] = [mask_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                masked_data[key] = value
                
        return masked_data
    
    # Apply masking to the entire event dict
    return mask_dict(event_dict)


def compliance_processor(logger, method_name, event_dict):
    """Add compliance metadata to log events."""
    
    # Add compliance tracking
    event_dict['compliance'] = {
        'pii_masked': True,
        'retention_class': 'standard',  # Could be 'sensitive', 'regulatory', etc.
        'audit_required': event_dict.get('level') in ['warning', 'error']
    }
    
    # Add correlation ID if not present
    if 'correlation_id' not in event_dict:
        import uuid
        event_dict['correlation_id'] = str(uuid.uuid4())
    
    return event_dict


def security_processor(logger, method_name, event_dict):
    """Add security context to log events."""
    
    # Security keywords categorized by severity
    high_severity_keywords = ['breach', 'attack', 'hack', 'exploit', 'malware', 'fraud']
    medium_severity_keywords = ['failed', 'unauthorized', 'forbidden', 'suspicious', 'blocked']
    low_severity_keywords = ['timeout', 'retry', 'throttled', 'rate_limit']
    
    event_text = str(event_dict.get('event', '')).lower()
    
    # Determine security alert level
    if any(keyword in event_text for keyword in high_severity_keywords):
        event_dict['security_alert'] = True
        event_dict['alert_level'] = 'high'
        event_dict['immediate_response_required'] = True
    elif any(keyword in event_text for keyword in medium_severity_keywords):
        event_dict['security_alert'] = True
        event_dict['alert_level'] = 'medium'
        event_dict['investigate_required'] = True
    elif any(keyword in event_text for keyword in low_severity_keywords):
        event_dict['security_alert'] = True
        event_dict['alert_level'] = 'low'
        event_dict['monitor_required'] = True
    
    # Add security context for financial thresholds
    if 'amount' in event_dict:
        amount = event_dict.get('amount', 0)
        if amount > 10000:  # Large transaction threshold
            event_dict['large_transaction_alert'] = True
            event_dict['aml_review_required'] = True  # Anti-Money Laundering
    
    # Check for rapid successive events (possible automation/bot)
    if 'attempt_count' in event_dict:
        attempts = event_dict.get('attempt_count', 0)
        if attempts > 3:
            event_dict['automation_suspected'] = True
            event_dict['captcha_required'] = True
    
    # Add threat intelligence context
    if 'ip_address' in event_dict:
        ip = event_dict.get('ip_address', '')
        # In real implementation, check against threat intelligence feeds
        if '10.0.0.' in ip or '192.168.' in ip:  # Example: private IPs are lower risk
            event_dict['ip_risk_level'] = 'low'
        else:
            event_dict['ip_risk_level'] = 'unknown'
    
    return event_dict

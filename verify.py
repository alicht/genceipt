#!/usr/bin/env python3
"""
PromptProof Receipt Verifier

This script verifies the authenticity of AI-generated receipts by recomputing
the SHA256 hash and comparing it against the stored hash.

Usage:
    python verify.py <receipt.json>
"""

import json
import hashlib
import sys
import os


def verify_receipt(receipt_path):
    """
    Verify the authenticity of a receipt JSON file.
    
    Args:
        receipt_path (str): Path to the receipt JSON file
        
    Returns:
        bool: True if receipt is valid, False if tampered
    """
    try:
        # Check if file exists
        if not os.path.exists(receipt_path):
            print(f"❌ Error: File '{receipt_path}' not found")
            return False
        
        # Load receipt JSON
        with open(receipt_path, 'r', encoding='utf-8') as f:
            receipt = json.load(f)
        
        # Validate required fields
        required_fields = ['timestamp', 'model', 'prompt', 'response', 'hash']
        missing_fields = [field for field in required_fields if field not in receipt]
        
        if missing_fields:
            print(f"❌ Error: Missing required fields: {', '.join(missing_fields)}")
            return False
        
        # Recompute hash
        hash_input = (
            receipt['timestamp'] + 
            receipt['model'] + 
            receipt['prompt'] + 
            receipt['response']
        )
        computed_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        # Compare hashes
        stored_hash = receipt['hash']
        
        if computed_hash == stored_hash:
            print("Receipt is valid ✅")
            print(f"✓ Timestamp: {receipt['timestamp']}")
            print(f"✓ Model: {receipt['model']}")
            print(f"✓ Hash: {computed_hash}")
            return True
        else:
            print("Tampered ❌")
            print(f"❌ Expected hash: {stored_hash}")
            print(f"❌ Computed hash: {computed_hash}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function to handle command line arguments and verify receipt."""
    if len(sys.argv) != 2:
        print("Usage: python verify.py <receipt.json>")
        print("\nExample:")
        print("  python verify.py receipt_2025-09-25T10-30-45-123Z.json")
        sys.exit(1)
    
    receipt_path = sys.argv[1]
    
    print(f"🔍 Verifying receipt: {receipt_path}")
    print("-" * 50)
    
    is_valid = verify_receipt(receipt_path)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
import os
import sys

# Add project root to sys.path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.parser import parse_receipt
from app.core.calculator import validate_claims, calculate_subtotals, calculate_charges

def run_tests():
    print("Running End-to-End Logic Test...")
    
    image_path = os.path.join("data", "test", "bon-test.jpg")
    
    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return False
        
    print(f"Parsing receipt: {image_path}")
    predicted = parse_receipt(image_path)
    
    if "error" in predicted:
        print(f"Error parsing receipt: {predicted['error']}")
        return False
        
    # Filter out zero-price items
    predicted["items"] = [i for i in predicted.get("items", []) if i.get("price", 0) > 0]
    
    print("\n--- Parsed Output ---")
    print(predicted)
    
    if not predicted["items"]:
        print("No items parsed! Test failed.")
        return False
        
    # Alice claims the first item, Bob claims the second (if available)
    claims = {
        "Alice": {
            predicted["items"][0]["name"]: 1
        }
    }
    
    if len(predicted["items"]) > 1:
        claims["Bob"] = {
            predicted["items"][1]["name"]: 1
        }
        
    print("\n--- Claims ---")
    print(claims)
    
    is_valid = validate_claims(claims, predicted["items"])
    print(f"\nClaims valid: {is_valid}")
    
    if not is_valid:
        print("Test failed: Claims invalid")
        return False
        
    subtotals = calculate_subtotals(claims, predicted["items"])
    print("\n--- Subtotals ---")
    print(subtotals)
    
    charges = calculate_charges(predicted.get("charges", []), subtotals)
    print("\n--- Splitted Charges ---")
    print(charges)
    
    print("\n--- Final Bill ---")
    for person in claims:
        total = subtotals[person] + charges[person]
        print(f"{person}: {total:.2f}")
        
    print("\n[SUCCESS] End-to-End Logic Test Passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)

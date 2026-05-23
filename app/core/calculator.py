def validate_claims(claims: dict, items: list) -> bool:
    item_lookup = {item["name"]: item for item in items}
    
    claimed_totals = {}
    for person, claimed_items in claims.items():
        for item_name, qty in claimed_items.items():
            if item_name not in claimed_totals:
                claimed_totals[item_name] = 0
            claimed_totals[item_name] += qty
            
    is_valid = True
    for item_name, total_claimed in claimed_totals.items():
        if item_name not in item_lookup:
            print(f"❌ '{item_name}' tidak ditemukan di struk")
            is_valid = False
            continue
            
        available = item_lookup[item_name]["quantity"]
        if total_claimed > available:
            print(f"❌ '{item_name}': total klaim {total_claimed} melebihi tersedia {available}")
            is_valid = False
            
    return is_valid

def calculate_subtotals(claims: dict, items: list) -> dict:
    item_lookup = {item["name"]: item for item in items}
    
    subtotals = {}
    for person, claimed_items in claims.items():
        subtotal = 0
        for item_name, claimed_qty in claimed_items.items():
            item = item_lookup.get(item_name)
            if item:
                unit_price = item["price"] / item["quantity"]
                subtotal += unit_price * claimed_qty
        subtotals[person] = subtotal
        
    return subtotals

def calculate_charges(charges: list, subtotals: dict) -> dict:
    total_subtotal = sum(subtotals.values())
    
    splitted_charges = {person: 0 for person in subtotals}
    
    if total_subtotal == 0:
        return splitted_charges
        
    for charge in charges:
        for person, subtotal in subtotals.items():
            splitted_charges[person] += (subtotal / total_subtotal) * charge["amount"]
            
    return splitted_charges

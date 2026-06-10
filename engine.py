import json

def handle_death(old_player):
    print("\n" + "="*30)
    print(f"THE LEGACY OF {old_player['name']}")
    print(f"Final Wealth: ${old_player['money']}")
    print(f"Final Debt: ${old_player['debt']}")
    print("="*30)

    # Determine the child's starting situation
    inheritance = old_player['money'] - old_player['debt']
    
    print("\nYou are now playing as the next generation.")
    new_name = input("Enter your heir's name: ")
    
    # Create the new player starting at age 0 (or 5)
    new_player = {
        "name": new_name,
        "gender": old_player["gender"], # Can be changed to choice
        "age": 5,
        "money": 0,
        "debt": 0 if inheritance > 0 else abs(inheritance),
        "fame": int(old_player["fame"] * 0.2), # Inherit 20% of parent's fame
        "looks": 50,
        "smarts": 50,
        "fitness": 50,
        "career": None,
        "grade": "C",
        "inventory": {"cars": [], "jewels": []},
        "is_alive": True
    }
    
    if inheritance > 0:
        new_player["money"] = inheritance
        print(f"You inherited a fortune of ${inheritance}!")
    else:
        print(f"Your parent died in debt. You owe the bank ${new_player['debt']}!")
        
    return new_player
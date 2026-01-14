from schemas.in_game import Item, SceneObject, ObjectType, DamageType

def test_models():
    print("Testing Item and SceneObject compatibility...")
    
    # Test creating an Item with optional scene fields
    item_with_scene_fields = Item(
        name="Magic Sword",
        quantity=1,
        is_equipped=False,
        description="A glowing sword with magical properties",
        damage_dice="1d8",
        damage_type=DamageType.FIRE,
        # Optional scene object fields
        obj_type=ObjectType.INTERACTABLE,
        state="glowing",
        is_locked=None,
        is_hidden=True,
        content=["spell_component"],
        tags=["magical", "cursed"]
    )
    
    print(f"Created Item with scene fields: {item_with_scene_fields.name}")
    print(f"  - Has obj_type: {item_with_scene_fields.obj_type}")
    print(f"  - Has state: {item_with_scene_fields.state}")
    print(f"  - Is hidden: {item_with_scene_fields.is_hidden}")
    
    # Test creating a SceneObject with optional inventory fields
    scene_obj_with_inventory_fields = SceneObject(
        id="treasure_chest_01",
        name="Ancient Chest",
        description="A dusty wooden chest with intricate carvings",
        obj_type=ObjectType.CONTAINER,
        state="closed",
        is_locked=True,
        is_hidden=False,
        content=["gold_coin", "potion_health"],
        tags=["trapped", "magic_item_inside"],
        # Optional inventory fields
        quantity=1,
        is_equipped=None,
        damage_dice=None,
        damage_type=None,
        item_description="A treasure chest that can be looted"
    )
    
    print(f"\nCreated SceneObject with inventory fields: {scene_obj_with_inventory_fields.name}")
    print(f"  - Has quantity: {scene_obj_with_inventory_fields.quantity}")
    print(f"  - Has item_description: {scene_obj_with_inventory_fields.item_description}")
    print(f"  - Has damage_dice: {scene_obj_with_inventory_fields.damage_dice}")
    
    # Test creating minimal versions of both models
    minimal_item = Item(name="Basic Dagger", damage_dice="1d4", damage_type=DamageType.PIERCING)
    minimal_object = SceneObject(id="rock_01", name="Rock", description="A simple rock")
    
    print(f"\nMinimal Item: {minimal_item.name}")
    print(f"Minimal SceneObject: {minimal_object.name}")
    
    print("\nAll tests passed! Models are compatible.")

if __name__ == "__main__":
    test_models()
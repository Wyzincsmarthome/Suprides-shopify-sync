def get_tags_for_product(product):
    tags = []

    brand = product.get("brand", "").strip()
    if brand:
        tags.append(brand)

    family = product.get("family", "").strip()
    if family:
        tags.append(family)

    sub_family = product.get("sub_family", "")
    if sub_family:
        tags.append(sub_family.strip())

    family_to_main = {
        "Assistentes Virtuais": "Casa Inteligente",
        "Campainha Inteligente": "Casa Inteligente",
        "Fechaduras Inteligentes": "Casa Inteligente",
        "Hubs Inteligentes": "Casa Inteligente",
        "Iluminação": "Casa Inteligente",
        "Interruptor Inteligente": "Casa Inteligente",
        "Motor Cortinas": "Casa Inteligente",
        "Painel Controlo": "Casa Inteligente",
        "Termostato Inteligente": "Casa Inteligente",
        "Tomadas": "Casa Inteligente",
        "Gadgets Inteligentes": "Casa Inteligente",
        "Auscultadores": "Gadgets",
        "Smartwatch": "Gadgets",
        "Cozinha": "Gadgets",
        "Gadgets P/ Animais": "Gadgets",
        "Gadgets Diversos": "Gadgets",
        "Aspiradores": "Gadgets",
        "Mini Aspirador": "Gadgets",
        "Aspirador Vertical": "Gadgets",
        "Aspirador Robô": "Gadgets",
    }

    main_cat = family_to_main.get(family, None)
    if main_cat:
        tags.append(main_cat)

    return tags

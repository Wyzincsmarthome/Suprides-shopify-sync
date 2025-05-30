def map_main_category(product_family):
    casa_inteligente = [
        "Assistentes Virtuais", "Campainha Inteligente", "Controlo Remoto",
        "Fechaduras Inteligentes", "Hubs Inteligentes", "Iluminação",
        "Interruptor Inteligente", "Motor Cortinas", "Painel Controlo",
        "Termostato Inteligente", "Tomadas", "Gadgets Inteligentes"
    ]
    gadgets = [
        "Aspiradores", "Aspirador Vertical", "Aspirador Robô", "Mini Aspirador",
        "Acessórios Aspiradores", "Auscultadores", "Cozinha", "Smartwatch",
        "Gadgets P/ Animais", "Gadgets Diversos"
    ]

    if product_family in casa_inteligente:
        return "Casa Inteligente"
    elif product_family in gadgets:
        return "Gadgets"
    else:
        return "Sem categoria principal"

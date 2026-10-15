from PIL import Image, ImageDraw
import os

def create_pwa_icon(size: int, output_path: str):
    # Cria imagem RGBA
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / 512.0

    # 1. Fundo Gradiente com cantos arredondados
    # Criamos máscara para cantos arredondados
    radius = int(112 * scale)
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)

    # Gera gradiente vertical/diagonal (#1E3A8A até #0284C7)
    base_grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        factor = y / size
        # Interpolação de cores (30, 58, 138) -> (37, 99, 235) -> (2, 132, 199)
        if factor < 0.5:
            f = factor * 2
            r = int(30 * (1 - f) + 37 * f)
            g = int(58 * (1 - f) + 99 * f)
            b = int(138 * (1 - f) + 235 * f)
        else:
            f = (factor - 0.5) * 2
            r = int(37 * (1 - f) + 2 * f)
            g = int(99 * (1 - f) + 132 * f)
            b = int(235 * (1 - f) + 199 * f)
        for x in range(size):
            base_grad.putpixel((x, y), (r, g, b, 255))

    img.paste(base_grad, (0, 0), mask)

    # 2. Desenho dos Prédios
    # Prédio esquerdo
    left_x0, left_y0, left_x1, left_y1 = int(110 * scale), int(210 * scale), int(200 * scale), int(390 * scale)
    draw.rounded_rectangle([left_x0, left_y0, left_x1, left_y1], radius=int(8 * scale), fill=(30, 41, 59, 255))

    # Janelas prédio esquerdo
    win_w = int(22 * scale)
    win_h = int(22 * scale)
    for wy in [int(235 * scale), int(275 * scale), int(315 * scale)]:
        draw.rounded_rectangle([int(125 * scale), wy, int(125 * scale) + win_w, wy + win_h], radius=int(4 * scale), fill=(56, 189, 248, 220))
        draw.rounded_rectangle([int(160 * scale), wy, int(160 * scale) + win_w, wy + win_h], radius=int(4 * scale), fill=(56, 189, 248, 220))

    # Prédio direito
    right_x0, right_y0, right_x1, right_y1 = int(312 * scale), int(230 * scale), int(402 * scale), int(390 * scale)
    draw.rounded_rectangle([right_x0, right_y0, right_x1, right_y1], radius=int(8 * scale), fill=(30, 41, 59, 255))

    # Janelas prédio direito
    for wy in [int(255 * scale), int(295 * scale), int(335 * scale)]:
        draw.rounded_rectangle([int(327 * scale), wy, int(327 * scale) + win_w, wy + win_h], radius=int(4 * scale), fill=(56, 189, 248, 220))
        draw.rounded_rectangle([int(362 * scale), wy, int(362 * scale) + win_w, wy + win_h], radius=int(4 * scale), fill=(56, 189, 248, 220))

    # Prédio Central
    mid_x0, mid_y0, mid_x1, mid_y1 = int(190 * scale), int(140 * scale), int(322 * scale), int(390 * scale)
    draw.rounded_rectangle([mid_x0, mid_y0, mid_x1, mid_y1], radius=int(10 * scale), fill=(15, 23, 42, 255))

    # Topo triangular prédio central
    roof_pts = [(int(190 * scale), int(140 * scale)), (int(256 * scale), int(95 * scale)), (int(322 * scale), int(140 * scale))]
    draw.polygon(roof_pts, fill=(56, 189, 248, 255))

    # Janelas prédio central
    c_win_w = int(24 * scale)
    c_win_h = int(24 * scale)
    for wy in [int(165 * scale), int(205 * scale), int(245 * scale), int(285 * scale)]:
        for wx in [int(212 * scale), int(250 * scale), int(288 * scale)]:
            draw.rounded_rectangle([wx, wy, wx + c_win_w, wy + c_win_h], radius=int(4 * scale), fill=(248, 250, 252, 240))

    # Porta principal
    draw.rounded_rectangle([int(238 * scale), int(340 * scale), int(274 * scale), int(390 * scale)], radius=int(4 * scale), fill=(56, 189, 248, 255))

    # Escudo de segurança no canto inferior direito
    badge_cx, badge_cy = int(370 * scale), int(360 * scale)
    badge_r = int(50 * scale)
    draw.ellipse([badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r], fill=(37, 99, 235, 255), outline=(255, 255, 255, 255), width=int(5 * scale))
    
    # Check mark no escudo
    p1 = (badge_cx - int(18 * scale), badge_cy + int(2 * scale))
    p2 = (badge_cx - int(6 * scale), badge_cy + int(14 * scale))
    p3 = (badge_cx + int(18 * scale), badge_cy - int(12 * scale))
    draw.line([p1, p2, p3], fill=(255, 255, 255, 255), width=int(7 * scale), joint="curve")

    # Garante pasta de destino
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"Gerado: {output_path} ({size}x{size})")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    icons_dir = os.path.join(base_dir, "frontend", "icons")
    create_pwa_icon(192, os.path.join(icons_dir, "icon-192.png"))
    create_pwa_icon(512, os.path.join(icons_dir, "icon-512.png"))
    create_pwa_icon(180, os.path.join(icons_dir, "apple-touch-icon.png"))

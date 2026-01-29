from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from endfield_essence_recognizer.game_data.weapon import (
    all_attribute_stats,
    all_secondary_stats,
    all_skill_stats,
    get_gem_tag_name,
)

templates_dir = Path("src/endfield_essence_recognizer/templates/generated")

if __name__ == "__main__":
    font = ImageFont.truetype(r"C:\Windows\Fonts\HarmonyOS_SansSC_Regular.ttf", size=22)
    for label in all_attribute_stats + all_secondary_stats + all_skill_stats:
        text = get_gem_tag_name(label, "CN")
        image = Image.new("L", (160, 24), color=0)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, font=font, fill=255)
        save_path = templates_dir / f"{label}.png"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(save_path)
        print(f"Saved template image: {save_path}")

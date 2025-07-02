import os
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from gtts import gTTS
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

def convert_image_to_audio_html(image_path, description, output_dir):
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    html_file = os.path.join(output_dir, f"{base_name}.html")
    audio_file = os.path.join(output_dir, f"{base_name}.mp3")

    # Generate TTS audio
    tts = gTTS(description)
    tts.save(audio_file)

    # Generate HTML
    html_content = f"""
    <html>
    <body>
        <img src="{os.path.basename(image_path)}" onclick="document.getElementById('audio').play()" style="cursor:pointer; max-width:100%; height:auto;" />
        <audio id="audio" src="{os.path.basename(audio_file)}" preload="auto"></audio>
        <p>{description}</p>
    </body>
    </html>
    """
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return html_file, audio_file

def process_pptx_images(pptx_path, output_dir="media_output"):
    os.makedirs(output_dir, exist_ok=True)
    prs = Presentation(pptx_path)
    image_count = 0

    for slide_num, slide in enumerate(prs.slides):
        shapes = list(slide.shapes)  # clone list to safely modify
        for shape in shapes:
            if shape.shape_type == 13:  # Picture
                image = shape.image
                image_bytes = image.blob
                image_ext = image.ext or 'jpg'

                # Save original image
                image_path = os.path.join(output_dir, f"image_{slide_num}_{image_count}.{image_ext}")
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)

                # Get description from Gemini
                try:
                    description = describe_image_gemini(image_bytes)
                except Exception as e:
                    print(f"[ERROR] Gemini failed for image {image_count}: {e}")
                    continue

                # Generate HTML and audio
                html_file, audio_file = convert_image_to_audio_html(image_path, description, output_dir)

                # Save original image position/dimensions before deleting
                left = shape.left
                top = shape.top
                width = shape.width
                height = shape.height

                # Remove original image
                slide.shapes._spTree.remove(shape._element)

                # Add clickable rectangle with the same size/position
                placeholder = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
                placeholder.fill.solid()
                placeholder.fill.fore_color.rgb = RGBColor(255, 255, 255)
                placeholder.line.fill.background()  # no border

                # Add description as text
                text_frame = placeholder.text_frame
                text_frame.clear()
                p = text_frame.paragraphs[0]
                run = p.add_run()
                run.text = "🔊 Click to hear description"
                run.font.name = "Arial"
                run.font.size = Pt(14)
                run.font.color.rgb = RGBColor(0, 0, 255)

                # Link to HTML file
                r_id = slide.part.relate_to(html_file, RT.HYPERLINK, is_external=True)
                placeholder.click_action.hyperlink.address = html_file

                print(f"[INFO] Replaced image {image_count} on slide {slide_num}")
                image_count += 1

    # Save updated presentation
    new_pptx = os.path.join(output_dir, f"updated_{os.path.basename(pptx_path)}")
    prs.save(new_pptx)
    print(f"[DONE] Updated presentation saved: {new_pptx}")



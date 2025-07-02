import win32com.client
import os

def create_ppt_with_image_audio(image_path, audio_path, output_ppt_path):
    # Validate file paths
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Initialize PowerPoint application
    ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    ppt_app.Visible = True  # Make PowerPoint visible (optional for debugging)

    try:
        # Create a new presentation
        presentation = ppt_app.Presentations.Add()

        # Add a blank slide (layout 12 is Blank in PowerPoint)
        slide = presentation.Slides.Add(1, 12)  # 12 = ppLayoutBlank

        # Add the image to the slide
        image = slide.Shapes.AddPicture(
            FileName=os.path.abspath(image_path),
            LinkToFile=False,  # Embed the image
            SaveWithDocument=True,
            Left=50,  # Position in points
            Top=50,
            Width=200,  # Width in points
            Height=200   # Height in points
        )

        # Add the audio file to the slide
        audio = slide.Shapes.AddMediaObject2(
            FileName=os.path.abspath(audio_path),
            LinkToFile=False,  # Embed the audio
            SaveWithDocument=True,
            Left=-500,  # Position far off-slide to ensure hidden
            Top=-500
        )

        # Hide the audio icon during the slide show
        try:
            audio.AnimationSettings.PlaySettings.HideWhileNotPlaying = True
        except Exception as e:
            print(f"Warning: Could not set HideWhileNotPlaying: {e}")

        # Attempt to add an animation to play the audio when the image is clicked
        try:
            timeline = slide.TimeLine
            # Add a sequence for animations
            sequence = timeline.MainSequence
            # Add a placeholder animation for the image to enable triggering
            image_effect = sequence.AddEffect(
                Shape=image,
                EffectType=1,  # 1 = msoAnimEffectAppear (placeholder animation)
                TriggerType=2  # 2 = msoAnimTriggerOnShapeClick
            )
            # Add the play media animation for the audio, triggered after the image
            audio_effect = sequence.AddEffect(
                Shape=audio,
                EffectType=49,  # 49 = msoAnimEffectMediaPlay (Play Media)
                TriggerType=4   # 4 = msoAnimTriggerAfterPrevious
            )
            # Ensure the audio effect follows the image click
            audio_effect.Timing.TriggerShape = image
        except Exception as e:
            print(f"Warning: Could not set animation for image click: {e}")
            print("Manual steps required in PowerPoint to set audio to play on image click:")
            print("1. Open the generated presentation in PowerPoint.")
            print("2. Select the image, go to Animations > Add Animation > Appear.")
            print("3. In the Animation Pane, set the animation to trigger 'On Click of' the image.")
            print("4. Select the audio icon, go to Animations > Play.")
            print("5. In the Animation Pane, set the Play animation to start 'After Previous'.")
            print("6. Save the presentation.")

        # Save the presentation
        presentation.SaveAs(os.path.abspath(output_ppt_path))
        print(f"Presentation saved as {output_ppt_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise

    finally:
        # Close the presentation and quit PowerPoint
        presentation.Close()
        ppt_app.Quit()
        
# Example usage
if __name__ == "__main__":
    image_file = "banana.jpg"  # Replace with your image path
    audio_file = "out.wav"  # Replace with your audio path
    output_file = "output_presentation.pptx"  # Output file name
    create_ppt_with_image_audio(image_file, audio_file, output_file)
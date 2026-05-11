from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx.all as vfx

app = FastAPI()

class Scene(BaseModel):
    mp4_link: str
    mp3_link: str
    narration: str

def download_file(url, filename):
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: f.write(chunk)
    return filename

@app.post("/render")
def render_video(scenes: list[Scene]):
    clips = []
    
    for i, scene in enumerate(scenes):
        # 1. Download raw files
        vid_path = download_file(scene.mp4_link, f"vid_{i}.mp4")
        aud_path = download_file(scene.mp3_link, f"aud_{i}.mp3")
        
        video = VideoFileClip(vid_path)
        audio = AudioFileClip(aud_path)
        
        # 2. Sync Video to Audio Length (Loop if too short, trim if too long)
        if video.duration < audio.duration:
            video = video.fx(vfx.loop, duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)
            
        video = video.set_audio(audio)
        
        # 3. Generate Subtitles (Bold, White Text, Black Background)
        txt_clip = TextClip(
            scene.narration, 
            fontsize=60, 
            color='white', 
            bg_color='rgba(0,0,0,0.6)', 
            font='Liberation-Sans-Bold', 
            method='caption', 
            size=(video.w * 0.8, None)
        )
        txt_clip = txt_clip.set_position('center').set_duration(audio.duration)
        
        # 4. Stitch scene together
        final_scene = CompositeVideoClip([video, txt_clip])
        clips.append(final_scene)
        
    # 5. Connect all scenes into one full Short
    final_video = concatenate_videoclips(clips, method="compose")
    output_filename = "final_short.mp4"
    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
    
    # 6. Upload the final video to file.io (Free temporary file host)
    with open(output_filename, "rb") as f:
        response = requests.post("https://file.io", files={"file": f})
        data = response.json()
        
    # Clean up massive files from the server
    os.remove(output_filename)
    
    return {"youtube_ready_link": data.get("link", "Error uploading")}

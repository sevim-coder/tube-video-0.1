# YouTube Video Bot

This project creates themed videos automatically using text, images, and audio from various sources.

## Features
- Prompts the user to choose one of seven topics.
- Gathers content from global women's magazines and Wikipedia.
- Generates a 1500 word script split into scenes with titles.
- Downloads themed images from Pexels, Unsplash and Pixabay.
- Converts scene texts to speech via OpenAI TTS (or Google Cloud TTS).
- Mixes narration with random background music.
- Assembles a 1080p video using the images and audio.
- Saves all outputs under `output/<topic>/<timestamp>/`.

## Setup
1. Add your API keys to environment variables:
   - `OPENAI_API_KEY` – OpenAI API key.
   - `PEXELS_API_KEY` – Pexels API key.
   - `UNSPLASH_ACCESS_KEY` – Unsplash API key.
   - `PIXABAY_API_KEY` – Pixabay API key.
   - `GOOGLE_APPLICATION_CREDENTIALS` – optional Google Cloud credentials JSON file for TTS if OpenAI TTS is unavailable.
2. Place background music files (`.mp3`) in `assets/music/`.
3. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the bot from the repository root:
```bash
python main.py
```
Follow the on-screen instructions to select a topic and generate the video. All generated files will be saved under `output/<topic>/<timestamp>/`.

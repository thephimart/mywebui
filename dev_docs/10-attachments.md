# Attachments & Ingestion

## Libraries

- **OCR**: rapidocr
- **STT**: faster-whisper
- **Video**: ffmpeg-python
- **TTS**: Kokoro

## Supported Formats & Processing

### Images (jpg, png, gif, webp)

1. Save original to attachments
2. Generate thumbnail (256px)
3. Extract EXIF metadata
4. Run OCR (rapidocr) → extract text
5. Generate image embedding (if image embedding model configured)
6. Create chunk with text + media_ref

### Audio (mp3, wav, ogg, flac)

1. Save original to attachments
2. Transcribe to text (faster-whisper)
3. Create chunk with transcribed text

### Video (mp4, webm, mov)

1. Save original to attachments
2. Extract audio → transcribe (faster-whisper)
3. Generate thumbnail at 10s mark
4. Create chunk with transcribed text + thumbnail ref

### Documents (txt, md, pdf, docx)

1. Save original to attachments
2. Extract text based on type:
   - txt/md: direct read
   - pdf: pdfplumber or similar
   - docx: python-docx
3. Chunk text (500-800 tokens)
4. Generate text embeddings
5. Create chunks

## Storage (Local Filesystem)

```
~/.mywebui/users/<username>/attachments/
  <attachment_id>/
    original.<ext>
    thumbnail.jpg    # for images/video
```

## Output

- **TTS (Text-to-Speech)** - Convert text responses to audio
  - Trigger: User-initiated (not automatic)
  - Models: Configurable, default small

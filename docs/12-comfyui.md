# ComfyUI Integration

## Configuration

```yaml
comfyui:
  mode: local | remote
  url: http://localhost:8188  # default for local
  limits:
    max_steps: 100
    max_resolution: 1024
    allowed_seeds: [0, 42, 12345]
```

- **Local** by default (fits local-first philosophy)
- **Remote** URL allowed (transport change only)

## Workflow Definition

Workflows are JSON files stored in config:

```
config/workflows/
  portrait.json
  landscape.json
```

### Workflow Schema

```json
{
  "name": "Portrait Generator",
  "description": "Generate portrait images",
  "input_schema": {
    "prompt": "string",
    "seed": "integer",
    "steps": "integer"
  },
  "workflow": { ... }  # ComfyUI JSON
}
```

## API

```
POST /api/comfyui/run
{
  "workflow": "portrait",
  "input": {
    "prompt": "a photo of ...",
    "seed": 42,
    "steps": 20
  }
}
Response: { "job_id": "abc123" }

GET /api/comfyui/status/abc123
Response: { 
  "status": "queued|running|completed|failed",
  "progress": 0.5,
  "outputs": {
    "image": "base64 or url"
  }
}
```

## Security

- Admin-only access to run workflows
- Input validation against schema
- Enforce limits (steps, resolution, seeds)
- Timeout on long-running jobs

## Libraries

- **HTTP**: httpx

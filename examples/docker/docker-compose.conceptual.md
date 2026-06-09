# Conceptual Docker Compose Configuration

This is a CONCEPTUAL docker-compose.yml demonstrating the architecture. 
It is NOT production-ready and should NOT be deployed as-is.

For actual deployment, you would need to:
- Specify actual image names and registries
- Add proper credentials management
- Implement health checks
- Set resource limits
- Configure logging drivers
- Implement backup strategies

## Expected Structure

```yaml
version: '3.8'

services:
  django:
    # Django web application
    # - Serves user interface
    # - Manages configuration
    # - Exposes results
    ports:
      - "8000:8000"
    volumes:
      - shared_data:/data/shared
    depends_on:
      - postgres

  fastapi:
    # FastAPI AI orchestration service
    # - Coordinates training/inference
    # - Manages GPU access
    # - Integrates ClearML
    ports:
      - "8001:8001"
    volumes:
      - shared_data:/app/web_service/outputs
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all

  postgres:
    # PostgreSQL database
    # - Stores Django models
    # - Stores ClearML metadata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  shared_data:
    # Shared storage for artifacts
    # - Models
    # - Checkpoints
    # - Outputs
  postgres_data:
    # PostgreSQL persistent storage
```

## Mount Point Strategy

- **FastAPI path**: `/app/web_service/outputs/`
- **Django path**: `/data/shared/`
- **Both must reference the same physical storage**

## Environment Variables

See `environment.example.env`

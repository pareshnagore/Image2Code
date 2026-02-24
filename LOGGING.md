# Logging Documentation

## Overview

Image2Code uses **loguru** for structured, production-ready logging. The logging system is centralized, configurable, and designed to track the entire code extraction pipeline for debugging and production monitoring.

**Key Features:**
- Structured logging with timestamps, log levels, module names
- File-based logging with automatic rotation
- Console output in development/debug modes
- JSON output for production (machine-parseable)
- Configuration via YAML file + environment variable overrides
- No business logic changes - purely observational logging

---

## Quick Start

### 1. Basic Setup

Logging is automatically initialized when you run the application:

```bash
python main.py Images/
```

Logs will be written to `logs/app.log`

### 2. Viewing Logs

```bash
# Real-time tail
tail -f logs/app.log

# View today's log
cat logs/app.log

# Search for errors
grep ERROR logs/app.log
```

### 3. Changing Log Level

#### Option A: Environment Variable (Temporary)
```bash
LOG_LEVEL=DEBUG python main.py Images/
```

#### Option B: Config File (Permanent)
Edit `logging_config.yaml`:
```yaml
log_level: DEBUG
```

### 4. Log Format

#### Option A: Human-Readable (Development)
```bash
LOG_FORMAT=plain python main.py Images/
```

Output:
```
2026-02-24 10:34:56 | INFO     | core.pipeline:run:103 - Starting extraction | image_count: 3
2026-02-24 10:34:57 | DEBUG    | core.extractor:_extract_llm:181 - LLM extraction starting | model: qwen3-vl:235b-cloud | image: Images/code1.png
```

#### Option B: Machine-Readable JSON (Production)
```bash
LOG_FORMAT=json python main.py Images/
```

Output:
```json
{
  "timestamp": "2026-02-24T10:34:56.789123Z",
  "level": "INFO",
  "module": "core.pipeline",
  "function": "run",
  "line": 103,
  "message": "Starting extraction | image_count: 3"
}
```

---

## Configuration

### Configuration File: `logging_config.yaml`

Located at workspace root, controls logging behavior:

```yaml
version: 1
environment: dev              # dev, prod, debug

log_directory: logs           # Where to store logs
log_level: DEBUG              # DEBUG, INFO, WARNING, ERROR
log_format: plain             # plain or json

rotation:
  type: daily                 # daily or size
  retention: all              # all or "7 days"
```

### Environment Variables (Override Config File)

All must be prefixed with uppercase:

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Minimum log level |
| `LOG_FORMAT` | plain, json | plain | Output format |
| `LOG_DIRECTORY` | any path | logs/ | Log file location |
| `ENVIRONMENT` | dev, prod, debug | dev | Environment type |

**Priority:** Environment Variables > YAML Config > Defaults

### Example Configurations

#### Development (verbose, local disk)
```bash
LOG_LEVEL=DEBUG LOG_FORMAT=plain ENVIRONMENT=dev python main.py Images/
```

#### Production (info level, JSON format)
```bash
LOG_LEVEL=INFO LOG_FORMAT=json ENVIRONMENT=prod python main.py Images/
```

#### Troubleshooting (max verbosity)
```bash
LOG_LEVEL=DEBUG LOG_FORMAT=plain ENVIRONMENT=debug python main.py Images/
```

---

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| `DEBUG` | Detailed info for debugging | Image encoding size, LLM response details, overlap detection |
| `INFO` | General workflow events | Pipeline start/complete, extraction success, blocks created |
| `WARNING` | Potential issues, fallbacks | JSON parsing fallback, overlap strategy fallback |
| `ERROR` | Errors that should be fixed | LLM API failure, invalid image path, parsing errors |
| `CRITICAL` | System-level failures | Unrecoverable errors (rare) |

---

## What Gets Logged

### Core Pipeline (core/pipeline.py)
```
✓ Pipeline start/complete
✓ Each stage start/complete (extraction, ordering, reconstruction)
✓ Block counts at each stage
✓ Timing information (stages)
```

### Image Extraction (core/extractor.py)
```
✓ Extraction start/complete
✓ Per-image LLM call start/complete
✓ JSON parsing success/failure
✓ Fallback to raw text (if needed)
✓ Image metadata (format, language, cells)
✓ Failed images count
```

### Block Ordering (core/ordering.py)
```
✓ Ordering start/complete
✓ Strategy used (line_numbers > timestamp > overlap > fallback)
✓ Blocks successfully ordered
```

### Block Grouping (core/grouping.py)
```
✓ Grouping start/complete
✓ Groups created count
✓ Per-group details (blocks, total lines)
```

### Code Reconstruction (core/reconstruction.py)
```
✓ Reconstruction type (notebook vs code)
✓ Block processing (per-block details)
✓ Overlap detection and merge count
✓ Final code statistics (line count)
```

---

## Example Log Flow

Here's a complete run logged from start to finish:

```
2026-02-24 10:34:56 | INFO  | __main__:main:50 - ============================================================
2026-02-24 10:34:56 | INFO  | __main__:main:51 - Code Extraction Pipeline Started
2026-02-24 10:34:56 | INFO  | __main__:main:52 - Arguments: ['Images/']

2026-02-24 10:34:56 | INFO  | __main__:main:62 - Found 3 image(s) to process

2026-02-24 10:34:56 | INFO  | core.pipeline:run:107 - Pipeline started | image_paths: 3

2026-02-24 10:34:56 | INFO  | core.pipeline:extract_blocks:28 - Starting extraction | image_count: 3
2026-02-24 10:34:56 | INFO  | core.extractor:extract_from_images:231 - Starting extraction from images | count: 3
2026-02-24 10:34:56 | DEBUG | core.extractor:extract_from_images:234 - Extracting image 1/3 | path: Images/code1.png
2026-02-24 10:34:56 | INFO  | core.extractor:_extract_llm:177 - Calling LLM model: qwen3-vl:235b-cloud
2026-02-24 10:34:58 | DEBUG | core.extractor:_extract_llm:185 - LLM response received | response_size: 1850
2026-02-24 10:34:58 | DEBUG | core.extractor:extract_from_image:206 - JSON parsed successfully | format: python | cells: 1
2026-02-24 10:34:58 | INFO  | core.extractor:extract_from_image:223 - Block extracted | format: python | lines: 45

... [similar for images 2 and 3] ...

2026-02-24 10:35:02 | INFO  | core.extractor:extract_from_images:245 - Extraction complete | success: 3 | failed: 0

2026-02-24 10:35:02 | INFO  | core.pipeline:order_blocks:37 - Starting ordering | block_count: 3
2026-02-24 10:35:02 | INFO  | core.ordering:order:25 - Starting block ordering | block_count: 3
2026-02-24 10:35:02 | INFO  | core.ordering:order:31 - Ordering strategy: LINE_NUMBERS | blocks: 3
2026-02-24 10:35:02 | INFO  | core.pipeline:order_blocks:39 - Ordering complete | blocks_ordered: 3

2026-02-24 10:35:02 | INFO  | core.pipeline:reconstruct:43 - Starting reconstruction | block_count: 3 | format: python
2026-02-24 10:35:02 | INFO  | core.reconstruction:reconstruct:31 - Reconstruction type: CODE
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:57 - Processing code block 1/3 | lines: 45
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:68 - First block appended | total_lines: 45
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:73 - Processing code block 2/3 | lines: 50
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:78 - Overlap detected | block: 2 | overlap_lines: 3
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:81 - Block merged | total_lines: 92
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:73 - Processing code block 3/3 | lines: 55
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:78 - Overlap detected | block: 3 | overlap_lines: 2
2026-02-24 10:35:02 | DEBUG | core.reconstruction:_reconstruct_code:81 - Block merged | total_lines: 145
2026-02-24 10:35:02 | INFO  | core.reconstruction:_reconstruct_code:84 - Code reconstruction complete | final_lines: 145 | filename: script.py

2026-02-24 10:35:02 | INFO  | core.pipeline:reconstruct:44 - Reconstruction complete | status: success

2026-02-24 10:35:02 | INFO  | __main__:save_output:38 - Output saved successfully | path: outputs/script.py

2026-02-24 10:35:02 | INFO  | __main__:main:77 - Reconstruction complete | saved to: outputs/script.py
```

---

## Analyzing Logs

### Find Errors Only
```bash
grep ERROR logs/app.log
```

### Find Specific Module
```bash
grep core.extractor logs/app.log
```

### Find Specific Image
```bash
grep "code1.png" logs/app.log
```

### Find LLM Calls
```bash
grep "Calling LLM" logs/app.log
```

### Find Ordering Strategy Used
```bash
grep "Ordering strategy:" logs/app.log
```

### Find Overlaps Detected
```bash
grep "Overlap detected" logs/app.log
```

### Count Failures
```bash
grep ERROR logs/app.log | wc -l
```

### Performance: Find slowest image
```bash
grep "LLM response received" logs/app.log
```

---

## Production Deployment

### Setup for Production

1. **Use JSON format for log aggregation:**
   ```bash
   # Update .env or environment:
   export LOG_FORMAT=json
   export LOG_LEVEL=INFO
   export ENVIRONMENT=prod
   ```

2. **Store logs in persistent location:**
   ```bash
   # Configure in logging_config.yaml:
   log_directory: /var/log/image2code/
   ```

3. **Setup log rotation:**
   ```yaml
   rotation:
     type: daily        # or "size" with size parameter
     retention: "30 days"  # or "all"
   ```

4. **Redirect to external logging service (future enhancement):**
   - JSON logs can be easily piped to ELK Stack, Datadog, etc.
   - Use: `tail -f logs/app.log | send-to-logging-service`

### Monitoring in Production

**Watch for:**
- ERROR logs → immediate attention needed
- WARNING logs → potential issues to investigate
- Extraction failures → check LLM availability
- High overlap counts → possible duplicate detection issues

---

## Troubleshooting

### Logs not appearing

1. **Check log directory exists:**
   ```bash
   ls -la logs/
   ```

2. **Check file permissions:**
   ```bash
   chmod 755 logs/
   ```

3. **Verify environment variables:**
   ```bash
   echo $LOG_LEVEL
   echo $LOG_FORMAT
   ```

4. **Check configuration file:**
   ```bash
   cat logging_config.yaml
   ```

### Too much output

Change log level:
```bash
LOG_LEVEL=WARNING python main.py Images/
```

### JSON format too verbose

Use plain format for development:
```bash
LOG_FORMAT=plain python main.py Images/
```

### Console not showing logs

Ensure ENVIRONMENT is dev/debug, not prod:
```bash
ENVIRONMENT=dev python main.py Images/
```

---

## For Developers

### Add Logging to New Code

1. **Import logger:**
   ```python
   from core.logger import get_logger
   logger = get_logger(__name__)
   ```

2. **Use appropriate level:**
   ```python
   logger.debug("Variable values", extra={"var1": value1})
   logger.info("Stage complete", extra={"stage": "extraction"})
   logger.warning("Fallback used", extra={"reason": "missing data"})
   logger.error("LLM failed", extra={"error": str(e)})
   ```

3. **Add context with extra dict:**
   ```python
   logger.info(
       "Processing image",
       extra={
           "image": image_path,
           "format": detected_format,
           "cells": cell_count
       }
   )
   ```

### Testing Logging

```python
# test_logging.py
import os
os.environ['LOG_LEVEL'] = 'DEBUG'

from core.logger import initialize_logger, get_logger
initialize_logger()

logger = get_logger("test")
logger.debug("Test debug message")
logger.info("Test info message")
logger.warning("Test warning message")
logger.error("Test error message")
```

Run: `python test_logging.py` and check `logs/app.log`

---

## Summary

- **Easy to use**: `from core.logger import get_logger` and log away
- **Zero logic changes**: Pure observation, no business logic modified
- **Flexible configuration**: YAML + environment variables
- **Production ready**: JSON output, automatic rotation
- **Comprehensive**: Every stage of pipeline tracked
- **Debuggable**: Detailed logs for troubleshooting multi-image processing

---

**Need Help?**
- Check logs: `cat logs/app.log`
- View recent errors: `tail -20 logs/app.log`
- Search logs: `grep -i "error\|warning" logs/app.log`

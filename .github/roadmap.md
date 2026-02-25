✅ V2 To-Do List 

1. Partial Line Overlap Handling

Improve overlap detection to handle cases where a line is split across two images (prefix/suffix matching instead of exact match).

2. Normalized Overlap Comparison

Before deduplication, normalize whitespace and minor OCR variations to improve match robustness.

3. Gap Detection

Detect missing line number ranges between consecutive blocks and raise warning or reduce confidence.

4. Out-of-Order Detection

After ordering, verify monotonic increase of start_line to detect incorrect ordering.

5. Line Continuity Verification

Check that consecutive blocks follow expected numeric continuity (end_line + 1). if not, then its either overlap or gap or duplicate block or wrong ordering. 

6. Reconstruction Confidence Scoring

Introduce scoring system based on:

overlap confidence

gap presence

ordering correctness

metadata completeness

7. Structured Validation Layer

Add reconstruction_validator module to centralize:

gap checks

order checks

continuity checks

scoring

8. Batch Mode (Multi-file Support)

Support reconstruction of multiple independent scripts i.e. output file in a single run.

9. Notebook Cell Boundary Validation

Improve detection and merging of notebook cells split across images.

10. UI Confidence Display

Expose reconstruction confidence and warnings in UI.



**UI Instructions later**
- First thing first, click as much as crisp photos. Blury images may give suboptimal outputs (garbage in, garbage out lol)
- Enable line number visibility in your IDE (vscode, cursor, notepad++, etc). It helps ordering and validation.
- Include tab name or file name in image, so that AI can can output original filename as it is. 
- Make sure no lines are missed across images. i.e. image 1 ends at 50 and image 2 starts at 60, then those 10 lines are gone. Overlap is fine, in fact little overlap is good to have. It helps ordering and validation. 
- Try to click the images sequencially from top to bottom. Image timestamps is one of the fallback logic. 
- If possible, click photos in light theme. Contrast detection and OCR is better. 
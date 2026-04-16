# Usage Examples

## Scanning Images

```bash
# Basic scan
pixsize scan ./my-images

# JSON output for scripting
pixsize scan ./sprites -o json | jq '.[] | select(.width > 100)'

# Find all square PNGs between 32x32 and 256x256
pixsize scan ./icons --format PNG --square --min-width 32 --max-width 256

# Find large images for optimization
pixsize scan ./web-assets --min-mp 2.0 -o csv > large-images.csv
```

## Validating Images

```bash
# Check sprite tiles are square PNGs <= 256px
pixsize check ./sprites --square --max-width 256 --format PNG

# Validate against YAML rules
pixsize check ./assets --rules sprite-rules.yaml

# Check multiple paths
pixsize check ./icons ./logos ./banners --min-width 64 --max-height 512
```

## Resizing Images

```bash
# Resize to Full HD
pixsize resize ./photos -o ./output --preset fhd

# Create app icons at multiple sizes
for size in 16 32 64 128 256 512; do
  pixsize resize logo.png -o ./icons --preset icon-$size
done

# Max dimension for thumbnails
pixsize resize ./gallery -o ./thumbs --max-dim 200

# Force exact dimensions (stretch)
pixsize resize banner.png -o ./output -w 1200 -h 300 --no-keep-aspect
```

## Renaming Images

```bash
# Preview rename (dry run by default)
pixsize rename ./assets --pattern "{w}x{h}_{name}{ext}"

# Rename with sequential numbering
pixsize rename ./photos --pattern "photo_{i:04d}{ext}" --no-dry-run

# Rename with date prefix
pixsize rename ./screenshots --pattern "{date}_{name}{ext}" --no-dry-run
```

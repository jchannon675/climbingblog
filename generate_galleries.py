import argparse
import re
from pathlib import Path

# Hugo project configuration
CONTENT_DIR = Path("content/post")

GALLERY_HEADER = "## Photos in This Post"
GALLERY_OPEN = '{{< gallery columns="4" width="970px" >}}'
GALLERY_CLOSE = "{{< /gallery >}}"
PHOTOSWIPE = "{{< load-photoswipe >}}"

TOC_ENTRY = "- [Photos in This Post](#photos-in-this-post)"

# Match post-image shortcodes and their captions
POST_IMAGE_PATTERN = re.compile(
    r'\{\{<\s*post-image\b(?P<attrs>.*?)>\}\}'
    r'(?P<caption>.*?)'
    r'\{\{<\s*/post-image\s*>\}\}',
    re.DOTALL
)

# Extract quoted shortcode attributes
ATTRIBUTE_PATTERN = re.compile(
    r'(\w+)="([^"]*)"'
)

# Match Markdown TOC entries linking to headings within the same post
TOC_PATTERN = re.compile(
    r'^\s*[-*]\s+\[[^\]]+\]\(#[^)]+\)\s*$',
    re.MULTILINE
)


def extract_images(content):
    """Extract image URLs, alt text, and captions from post-image shortcodes."""

    images = []

    for match in POST_IMAGE_PATTERN.finditer(content):
        attrs = dict(ATTRIBUTE_PATTERN.findall(match.group("attrs")))

        image_url = attrs.get("image")
        alt = attrs.get("alt", "")
        caption = match.group("caption").strip()

        if not image_url:
            continue

        images.append({
            "image": image_url,
            "alt": alt,
            "caption": caption
        })

    return images


def add_toc_entry(content):
    """Add the Photos in This Post link to the existing TOC."""

    if TOC_ENTRY in content:
        print("  TOC entry already exists.")
        return content

    matches = list(TOC_PATTERN.finditer(content))

    if not matches:
        print("  WARNING: Could not find an existing TOC.")
        return content

    # Find the first contiguous block of TOC entries.
    first_match = matches[0]
    last_match = first_match

    for match in matches[1:]:
        between = content[last_match.end():match.start()]

        if between.strip():
            break

        last_match = match

    # Insert the new entry after the last entry in the TOC.
    insert_position = last_match.end()

    updated_content = (
        content[:insert_position]
        + "\n"
        + TOC_ENTRY
        + content[insert_position:]
    )

    print("  Added Photos in This Post to TOC.")

    return updated_content


def generate_gallery(images):
    """Generate a Hugo gallery from extracted images."""

    if not images:
        return ""

    lines = [
        GALLERY_HEADER,
        "",
        GALLERY_OPEN
    ]

    for item in images:
        image = item["image"]
        caption = item["caption"]

        # Escape quotes in shortcode attributes
        image = image.replace('"', '\\"')
        caption = caption.replace('"', '\\"')

        lines.append(
            f'  {{{{< figure src="{image}" '
            f'link="{image}" caption="{caption}" >}}}}'
        )

    lines.extend([
        GALLERY_CLOSE,
        "",
        PHOTOSWIPE
    ])

    return "\n".join(lines)


def process_post(path, write=False):
    """Process an individual Markdown post."""

    content = path.read_text(encoding="utf-8")

    # Avoid duplicating an existing generated gallery
    if GALLERY_HEADER in content:
        print(f"SKIP (gallery already exists): {path}")
        return

    images = extract_images(content)

    if not images:
        print(f"SKIP (no post-image shortcodes): {path}")
        return

    gallery = generate_gallery(images)

    # Add the gallery link to the existing TOC
    updated_content = add_toc_entry(content)

    # Append the gallery to the end of the post
    updated_content = updated_content.rstrip() + "\n\n" + gallery + "\n"

    print(f"{'UPDATED' if write else 'DRY RUN'}: {path}")
    print(f"  Images found: {len(images)}")

    if write:
        path.write_text(updated_content, encoding="utf-8")
    else:
        print("\n--- Generated gallery ---")
        print(gallery)
        print("-------------------------\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Hugo galleries from post-image shortcodes."
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Actually modify Markdown files. Default is dry-run."
    )

    parser.add_argument(
        "--post",
        type=str,
        help="Process only one Markdown post."
    )

    args = parser.parse_args()

    if args.post:
        posts = [Path(args.post)]
    else:
        posts = sorted(CONTENT_DIR.rglob("*.md"))

    if not posts:
        print("No Markdown posts found.")
        return

    print(f"Found {len(posts)} post(s).")
    print(f"Mode: {'WRITE' if args.write else 'DRY RUN'}\n")

    for post in posts:
        if not post.exists():
            print(f"NOT FOUND: {post}")
            continue

        process_post(post, write=args.write)

    if not args.write:
        print("\nDry run complete. No files were modified.")
        print("Run again with --write to apply changes.")


if __name__ == "__main__":
    main()
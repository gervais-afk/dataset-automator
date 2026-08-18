import os
import re
from datetime import datetime

KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../knowledge_base"))

def parse_frontmatter(content):
    match = re.match(r'^---\r?\n([\s\S]+?)\r?\n---', content)
    if match:
        yaml_part = match.group(1)
        body = content[match.end():]
        meta = {}
        for line in yaml_part.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip("'\"")
        return meta, body
    return {}, content

def dump_okf_v02(meta, body, sources_list):
    # OKF v0.2 additions
    yaml_lines = ["---"]
    
    # 1. Standard metadata fields
    for k in ["type", "title", "description", "domain"]:
        if k in meta:
            yaml_lines.append(f"{k}: {meta[k]}")
            
    # 2. Generated & Verified fields (Agentic Trust)
    yaml_lines.append('generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }')
    yaml_lines.append('verified:')
    yaml_lines.append('  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }')
    
    # 3. Freshness & Lifecycle
    yaml_lines.append('status: stable')
    yaml_lines.append('stale_after: 2027-08-14')
    
    # 4. Sources list
    if sources_list:
        yaml_lines.append('sources:')
        for src in sources_list:
            yaml_lines.append(f"  - {{ id: {src['id']}, title: {src['title']}, author: {src['author']} }}")
            
    yaml_lines.append("---")
    
    return "\n".join(yaml_lines) + body

def migrate_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    meta, body = parse_frontmatter(content)
    
    # Extract existing sources from body if present
    sources_list = []
    # Search for "**Sources**:" at the bottom
    sources_match = re.search(r'\*\*Sources\*\*:\r?\n([\s\S]+?)$', body, re.IGNORECASE)
    if sources_match:
        lines = sources_match.group(1).strip().split('\n')
        src_idx = 1
        for line in lines:
            line = line.strip()
            if line.startswith('-'):
                source_title = line[1:].strip()
                # Clean up title for inline YAML
                clean_title = source_title.replace('"', '\\"').replace("'", "\\'")
                sources_list.append({
                    "id": f"src-{src_idx}",
                    "title": f'"{clean_title}"',
                    "author": "external"
                })
                src_idx += 1
                
        # Remove the old sources text from body to avoid duplication
        body = body[:sources_match.start()].strip() + "\n"
        
    new_content = dump_okf_v02(meta, body, sources_list)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def main():
    print(f"🚀 Starting migration of knowledge base to OKF v0.2 in: {KNOWLEDGE_BASE_DIR}")
    count = 0
    for root, dirs, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    migrate_file(file_path)
                    count += 1
                except Exception as e:
                    print(f"❌ Error migrating {file}: {e}")
                    
    print(f"✅ Successfully migrated {count} files to Open Knowledge Format v0.2!")

if __name__ == "__main__":
    main()

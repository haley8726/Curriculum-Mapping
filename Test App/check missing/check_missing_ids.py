# check_missing_ids.py

def load_ids(id_file):
    """Load CSU IDs from a file, one per line."""
    with open(id_file, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def load_transcript_text(transcript_file):
    """Load full transcript text as one string."""
    with open(transcript_file, "r", encoding="utf-8") as f:
        return f.read()


def find_missing_ids(id_file, transcript_file):
    ids = load_ids(id_file)
    transcript_text = load_transcript_text(transcript_file)

    missing_ids = [csu_id for csu_id in ids if csu_id not in transcript_text]
    return missing_ids


if __name__ == "__main__":
    id_file = "CSU_ID.txt"
    transcript_file = "Transcripts_BMSandHES.txt"

    missing = find_missing_ids(id_file, transcript_file)

    if missing:
        print("❌ Missing CSU IDs (not found in transcript file):")
        for csu_id in sorted(missing):
            print(csu_id)
    else:
        print("✅ All CSU IDs were found in the transcript file.")
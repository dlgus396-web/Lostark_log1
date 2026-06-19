from lib.supabase_client import get_supabase_client

def load_supported_classes():
    supabase = get_supabase_client()
    result = (
        supabase.table("supported_classes")
        .select("class_name, attack_type, is_supported")
        .eq("is_supported", True)
        .execute()
    )
    return result.data

def load_bosses():
    supabase = get_supabase_client()
    result = (
        supabase.table("bosses")
        .select("id, boss_code, raid_name, gate_no, difficulty, boss_display_name")
        .order("raid_name")
        .order("gate_no")
        .execute()
    )
    return result.data


def format_boss_display(boss: dict) -> str:
    """Format boss dict into display string like '세르카 1관문'.

    Falls back to cleaned boss_display_name if raid_name missing.
    Removes common difficulty words if present.
    """
    if not boss:
        return ""
    raid_name = boss.get("raid_name")
    gate_no = boss.get("gate_no")
    if raid_name:
        try:
            return f"{raid_name} {int(gate_no)}관문"
        except Exception:
            return f"{raid_name} {gate_no}관문"

    display = boss.get("boss_display_name") or ""
    # remove common difficulty words (English + Korean) to avoid showing difficulty
    cleaned = re.sub(r"\b(Nightmare|Hard|Normal|Easy|나이트메어|하드|노말)\b", "", display, flags=re.IGNORECASE).strip()
    return cleaned or display


def load_boss_map() -> dict:
    """Return dict mapping boss id -> formatted display name."""
    bosses = load_bosses() or []
    mapping = {}
    for b in bosses:
        try:
            mapping[b["id"]] = format_boss_display(b)
        except Exception:
            mapping[b.get("id")] = b.get("boss_display_name") or ""
    return mapping

def load_score_rules(class_name: str):
    supabase = get_supabase_client()
    result = (
        supabase.table("score_rules")
        .select("metric_name, weight")
        .eq("class_name", class_name)
        .eq("version", "v1")
        .eq("is_active", True)
        .execute()
    )
    return result.data

def load_baselines(class_name: str, boss_id: int):
    supabase = get_supabase_client()
    result = (
        supabase.table("scoring_baselines")
        .select(
            "class_name, boss_id, metric_name, baseline_median, baseline_q3, baseline_ceiling, baseline_best, source_type, version"
        )
        .eq("class_name", class_name)
        .eq("boss_id", boss_id)
        .eq("source_type", "external_na_logs")
        .eq("version", "v1")
        .execute()
    )
    return result.data

def load_ranking_records(class_name: str | None = None, boss_id: int | None = None):
    """Load ranking records (only those with video_url).
    
    Args:
        class_name: Optional filter by class name
        boss_id: Optional filter by boss ID
    
    Returns:
        List of combat records with non-empty video_url, sorted by final_score descending.
    """
    supabase = get_supabase_client()
    query = supabase.table("combat_records").select("*")
    
    if class_name is not None:
        query = query.eq("class_name", class_name)
    
    if boss_id is not None:
        query = query.eq("boss_id", boss_id)
    
    result = query.order("final_score", desc=True).execute()
    
    # Filter for non-empty video_url in Python
    filtered = [
        record for record in result.data
        if record.get("video_url") is not None
        and str(record.get("video_url")).strip() != ""
    ]
    
    return filtered

def load_mock_ranking_records():
    # mock 랭킹 데이터 반환
    return [
        {
            "rank": 1,
            "class_name": "블레이드",
            "raid_name": "세르카 1관문 Nightmare",
            "final_score": 98.5,
            "key_action_cpm": 6.2,
            "back_attack_rate": 80.0,
            "video_url": "https://youtu.be/mock1"
        },
        {
            "rank": 2,
            "class_name": "브레이커",
            "raid_name": "카제로스 1관문 Hard",
            "final_score": 95.0,
            "key_action_cpm": 3.1,
            "back_attack_rate": None,
            "video_url": "https://youtu.be/mock2"
        },
        {
            "rank": 3,
            "class_name": "아르카나",
            "raid_name": "세르카 2관문 Nightmare",
            "final_score": 90.0,
            "key_action_cpm": 21.0,
            "back_attack_rate": None,
            "video_url": "https://youtu.be/mock3"
        }
    ]

def load_mock_my_records():
    # mock 내 기록 데이터 반환
    return [
        {
            "created_at": "2026-05-27 10:00:00",
            "class_name": "블레이드",
            "raid_name": "세르카 1관문 Nightmare",
            "final_score": 98.5,
            "video_url": "https://youtu.be/mock1"
        },
        {
            "created_at": "2026-05-26 09:30:00",
            "class_name": "브레이커",
            "raid_name": "카제로스 1관문 Hard",
            "final_score": 95.0,
            "video_url": None
        }
    ]

def load_my_records(user_id: str):
    """Load combat records for a specific user.
    
    Filters by user_id and orders by created_at in descending order.
    Returns result.data from the query.
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("combat_records")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data

def insert_combat_record(record: dict):
    """Insert a combat record into the `combat_records` table.

    Raises exceptions from the client so callers can handle them.
    Returns the inserted row data (`result.data`).
    """
    supabase = get_supabase_client()
    result = supabase.table("combat_records").insert(record).execute()
    return result.data


def delete_combat_record(record_id: int | str, user_id: str):
    """Delete a combat record owned by the given user.

    Behavior:
      1) Convert record_id to int (raise ValueError if not possible)
      2) Verify the record exists and is owned by the given user
      3) Execute delete
      4) Re-query the record id to ensure deletion succeeded

    Returns a dict with keys:
      - success: bool
      - message: human-readable message
      - reason: optional machine-readable reason on failure
    """
    try:
        record_id = int(record_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("record_id must be an integer") from exc

    supabase = get_supabase_client()

    # 1) check ownership / existence before deletion
    pre_check = (
        supabase.table("combat_records")
        .select("id")
        .eq("id", record_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not pre_check.data:
        return {
            "success": False,
            "reason": "not_found_or_not_owner",
            "message": "현재 로그인 사용자의 기록을 찾을 수 없습니다.",
        }

    # 2) attempt delete
    _ = (
        supabase.table("combat_records")
        .delete()
        .eq("id", record_id)
        .eq("user_id", user_id)
        .execute()
    )

    # 3) verify deletion by re-querying the id
    post_check = (
        supabase.table("combat_records")
        .select("id")
        .eq("id", record_id)
        .execute()
    )

    if not post_check.data:
        return {"success": True, "message": "기록이 삭제되었습니다."}
    else:
        return {
            "success": False,
            "reason": "still_exists",
            "message": "삭제 후에도 기록이 DB에 남아 있습니다.",
        }


def insert_report(record_id: int, reporter_user_id: str, report_reason: str):
    """Insert a report (신고) into the `reports` table.
    
    Args:
        record_id: ID of the combat record being reported
        reporter_user_id: ID of the user submitting the report
        report_reason: Reason for the report
    
    Raises exceptions from the client so callers can handle them.
    Returns the inserted row data (`result.data`).
    """
    supabase = get_supabase_client()
    report = {
        "record_id": record_id,
        "reporter_user_id": reporter_user_id,
        "report_reason": report_reason,
    }
    result = supabase.table("reports").insert(report).execute()
    return result.data

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

"""Game file paths defined by the PRD and directory preparation."""

from pathlib import Path

from game_config import DIFFICULTIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAMEFILE_DIR = PROJECT_ROOT / "gamefile"
GUN_DIR = GAMEFILE_DIR / "gun"
COIN_DIR = GAMEFILE_DIR / "coin"
PLAYLOG_DIR = GAMEFILE_DIR / "playlog"

GUNS_PATH = GUN_DIR / "getGuns.txt"
UPGRADE_PATH = GUN_DIR / "LvGuns.txt"
COINS_PATH = COIN_DIR / "coins.txt"
BEST_LOG_PATH = PLAYLOG_DIR / "BestLog.txt"
RECENT_LOG_PATH = PLAYLOG_DIR / "latelyLog.txt"
TRAINING_LOG_PATH = PLAYLOG_DIR / "trainingLog.txt"
DIFFICULTY_PATH = PLAYLOG_DIR / "difficulty.txt"
# 난이도별 전투 기록: 사용한 총 / 클리어한 웨이브 / 클리어한 시간.
RECORDS_PATHS = {
    difficulty: PLAYLOG_DIR / "records_{}.txt".format(difficulty)
    for difficulty in DIFFICULTIES
}


def ensure_gamefile_directories(root=None):
    """Create the game file directories and return the base directory."""
    base = Path(root) if root is not None else GAMEFILE_DIR
    for directory in (base / "gun", base / "coin", base / "playlog"):
        directory.mkdir(parents=True, exist_ok=True)
    return base


def gamefile_paths(root=None):
    """Return all game file paths under the given gamefile root."""
    base = Path(root) if root is not None else GAMEFILE_DIR
    result = {
        "guns": base / "gun" / "getGuns.txt",
        "upgrades": base / "gun" / "LvGuns.txt",
        "coins": base / "coin" / "coins.txt",
        "best_log": base / "playlog" / "BestLog.txt",
        "recent_logs": base / "playlog" / "latelyLog.txt",
        "training_records": base / "playlog" / "trainingLog.txt",
        "difficulty": base / "playlog" / "difficulty.txt",
    }
    for difficulty, path in RECORDS_PATHS.items():
        result["records_{}".format(difficulty)] = base / "playlog" / path.name
    return result

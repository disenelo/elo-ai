"""
blender/state_visualiser.py — console presence visualiser.

Renders AvatarState + motion intent as a readable terminal snapshot.
Used by blender_bridge.py and standalone debug.
"""

_BAR_WIDTH  = 20
_FULL       = "█"
_EMPTY      = "░"


def _bar(value: float) -> str:
    filled = round(float(value) * _BAR_WIDTH)
    return _FULL * filled + _EMPTY * (_BAR_WIDTH - filled)


def show(state: dict, motion: dict = None) -> None:
    """Print a formatted presence snapshot to the console."""
    mode    = state.get("mode",        "?")
    energy  = float(state.get("energy",     0.0))
    curious = float(state.get("curiosity",  0.0))
    certain = float(state.get("certainty",  0.0))
    engaged = float(state.get("engagement", 0.0))

    print()
    print("  eLo presence ─────────────────────────────")
    print(f"  mode        {mode}")
    print(f"  energy      {_bar(energy)}  {energy:.2f}")
    print(f"  curiosity   {_bar(curious)}  {curious:.2f}")
    print(f"  certainty   {_bar(certain)}  {certain:.2f}")
    print(f"  engagement  {_bar(engaged)}  {engaged:.2f}")
    if motion:
        print()
        print(f"  motion      {motion.get('animation', '?')}")
        print(f"  duration    {motion.get('duration',  '?')}s")
        print(f"  intensity   {motion.get('intensity', '?')}")
    print("  ──────────────────────────────────────────")
    print()

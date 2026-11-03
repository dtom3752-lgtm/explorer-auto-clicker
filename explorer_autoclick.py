"""
explorer_autoclick.py - auto-dismiss Windows Explorer file-operation prompts.

Clicks, in priority order:
    1. Continue
    2. Skip (also "Skip this file" / "Skip these files")
    3. Try Again (limited to --max-retries, then falls back to Skip)

It NEVER clicks Replace, Overwrite, Cancel, etc.

Setup (once):   pip install pywinauto psutil
Run:            python explorer_autoclick.py
Debug:          python explorer_autoclick.py --debug
                (prints every Explorer dialog it sees plus its buttons/text;
                 keep a dialog open while it runs and paste the output back)
Stop with Ctrl+C.
"""
import argparse
import time

import psutil
from pywinauto import Desktop

PRIORITY = ["continue", "skip", "try again"]

# Big/irrelevant Explorer windows we don't want to scan every half second.
SKIP_CLASSES = {
    "CabinetWClass", "ExploreWClass", "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd", "Progman", "WorkerW",
    "NotifyIconOverflowWindow", "TopLevelWindowForOverflowXamlIsland",
}


def explorer_pids():
    return {p.pid for p in psutil.process_iter(["name"])
            if (p.info["name"] or "").lower() == "explorer.exe"}


def el_name(el):
    try:
        return (el.element_info.name or "").strip()
    except Exception:
        return ""


def el_type(el):
    try:
        return el.element_info.control_type or ""
    except Exception:
        return ""


def find_candidates(win):
    found = {}
    try:
        for el in win.descendants():
            name = el_name(el).lower()
            if not name:
                continue
            for key in PRIORITY:
                if name.startswith(key) and key not in found:
                    found[key] = el
    except Exception:
        pass
    return found


def press(el):
    try:
        el.invoke()
    except Exception:
        el.click_input()


def dump(win, seen):
    h = win.handle
    if h in seen:
        return
    seen.add(h)
    try:
        cls = win.element_info.class_name
    except Exception:
        cls = "?"
    print(f"\n--- window: title='{win.window_text()}' class='{cls}' "
          f"pid={win.process_id()}")
    try:
        for el in win.descendants():
            n = el_name(el)
            if n:
                print(f"      [{el_type(el)}] {n[:90]}")
    except Exception as e:
        print("      (could not read children:", e, ")")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--max-retries", type=int, default=3)
    ap.add_argument("--no-continue", action="store_true")
    ap.add_argument("--no-skip", action="store_true")
    ap.add_argument("--no-retry", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    allowed = set(PRIORITY)
    if args.no_continue:
        allowed.discard("continue")
    if args.no_skip:
        allowed.discard("skip")
    if args.no_retry:
        allowed.discard("try again")

    retries = 0
    last_action = time.time()
    seen = set()
    print("Watching Explorer dialogs. Ctrl+C to stop."
          + ("  [DEBUG ON]" if args.debug else ""))

    while True:
        try:
            if time.time() - last_action > 15:
                retries = 0
            pids = explorer_pids()
            for win in Desktop(backend="uia").windows():
                try:
                    if win.process_id() not in pids:
                        continue
                    if win.element_info.class_name in SKIP_CLASSES:
                        continue
                except Exception:
                    continue

                if args.debug:
                    dump(win, seen)

                cands = find_candidates(win)
                for key in PRIORITY:
                    if key not in allowed or key not in cands:
                        continue
                    if key == "try again":
                        if retries >= args.max_retries:
                            continue
                        retries += 1
                    press(cands[key])
                    last_action = time.time()
                    print(f"[{time.strftime('%H:%M:%S')}] "
                          f"'{win.window_text()}' -> {key}")
                    break
        except KeyboardInterrupt:
            print("Stopped.")
            return
        except Exception as e:
            print("warn:", e)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

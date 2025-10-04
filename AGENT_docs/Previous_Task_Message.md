favorite_select.py has been trimmed to remove any favorites-bar scrolling automation. It now:
- Scans ONLY the currently visible favorites for payout >= min_pct
- Optionally clicks eligible items on the current page (no pagination/scrolling)
- Provides a compact _scan_visible_favorites implementation
- Simplifies _click_favorite_simple to click only on the current page

What changed
- Removed paging_max_steps and paging_step_ratio inputs
- Removed use of HighPriorityControls in this capability
- Replaced scanning with a new _scan_visible_favorites(ctx, min_pct)
- Replaced the previous paging logic in _click_favorite_simple with a direct call to _click_favorite_on_current_page
- Kept robust click-by-label logic and verification

For scrolling the favorites bar, use the dedicated capability:
- favorites_bar_scroll.py (already created and working)

Examples (PowerShell)
- Selection on current page only:
  python .\capabilities\favorite_select.py --min-pct 92 --select all
- Scroll separately when needed:
  python .\capabilities\favorites_bar_scroll.py --direction to_end_right
  python .\capabilities\favorites_bar_scroll.py --direction reset_left

favorite_select is now strictly responsible for selecting favorites; all scroll automation has been removed as requested.
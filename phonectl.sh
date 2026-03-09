#!/bin/sh
# phonectl - 简化版手机控制工具（使用 input 命令代替 uinput）
# 适用于华为等不支持 uinput 的设备

export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

ADB_CMD="adb -s localhost:5555"
SCREENSHOT_DIR="/sdcard"
UIDUMP="/sdcard/window_dump.xml"

adb_shell() {
    $ADB_CMD shell "$@" 2>&1
}

case "$1" in
    # === Touch & Gesture ===
    tap)
        # phonectl tap <x> <y>
        adb_shell "input tap $2 $3"
        ;;
    longpress)
        # phonectl longpress <x> <y> [ms=1000]
        duration=${4:-1000}
        adb_shell "input swipe $2 $3 $2 $3 $duration"
        ;;
    swipe)
        # phonectl swipe <x1> <y1> <x2> <y2> [ms=300]
        duration=${6:-300}
        adb_shell "input swipe $2 $3 $4 $5 $duration"
        ;;
    scroll_up)
        adb_shell "input swipe 540 1600 540 800 400"
        ;;
    scroll_down)
        adb_shell "input swipe 540 800 540 1600 400"
        ;;

    # === Key Events ===
    key)
        adb_shell "input keyevent $2"
        ;;
    home)
        adb_shell "input keyevent KEYCODE_HOME"
        ;;
    back)
        adb_shell "input keyevent KEYCODE_BACK"
        ;;
    power)
        adb_shell "input keyevent KEYCODE_POWER"
        ;;
    enter)
        adb_shell "input keyevent KEYCODE_ENTER"
        ;;
    menu)
        adb_shell "input keyevent KEYCODE_MENU"
        ;;

    # === Screen Capture ===
    screenshot)
        filename=${2:-$SCREENSHOT_DIR/screen.png}
        adb_shell "screencap -p $filename"
        echo "$filename"
        ;;

    # === UI Inspection ===
    uidump)
        adb_shell "uiautomator dump /dev/tty" 2>/dev/null | grep -v "UI hierchary dumped"
        ;;
    uidump_text)
        adb_shell "uiautomator dump /dev/tty" 2>/dev/null | \
            grep -oP 'text="[^"]*"' | \
            sed 's/text="//;s/"$//' | \
            grep -v '^$' | \
            sort -u
        ;;
    find_text)
        keyword="$2"
        adb_shell "uiautomator dump /dev/tty" 2>/dev/null | \
            grep -oP "text=\"[^\"]*$keyword[^\"]*\"[^>]*bounds=\"\[[0-9,\[\]]+\]\"" | \
            sed 's/.*bounds="\[\([0-9]*\),\([0-9]*\)\]\[\([0-9]*\),\([0-9]*\)\]\]".*/\1 \2 \3 \4/' | \
            awk '{print "x="int(($1+$3)/2)" y="int(($2+$4)/2)}'
        ;;
    tap_text)
        keyword="$2"
        coords=$(adb_shell "uiautomator dump /dev/tty" 2>/dev/null | \
            grep -oP "text=\"[^\"]*$keyword[^\"]*\"[^>]*bounds=\"\[[0-9,\[\]]+\]\"" | \
            head -1 | \
            sed 's/.*bounds="\[\([0-9]*\),\([0-9]*\)\]\[\([0-9]*\),\([0-9]*\)\]\]".*/\1 \2 \3 \4/' | \
            awk '{print int(($1+$3)/2)" "int(($2+$4)/2)}')
        if [ -n "$coords" ]; then
            adb_shell "input tap $coords"
            echo "Tapped: $coords"
        else
            echo "Text not found: $keyword"
            exit 1
        fi
        ;;

    # === App Control ===
    current_app)
        adb_shell "dumpsys window | grep mCurrentFocus" | \
            sed 's/.*{[^}]*\s\([^/}]*\)\/\([^}]*\)}.*/\1/'
        ;;
    launch_pkg)
        adb_shell "monkey -p $2 -c android.intent.category.LAUNCHER 1"
        ;;
    open_url)
        adb_shell "am start -a android.intent.action.VIEW -d '$2'"
        ;;

    # === System Info ===
    shell)
        shift
        adb_shell "$@"
        ;;

    *)
        echo "Usage: phonectl <command> [args]"
        echo ""
        echo "Touch: tap / longpress / swipe / scroll_up / scroll_down"
        echo "Keys: home / back / power / enter / menu"
        echo "Screen: screenshot / uidump / uidump_text / find_text / tap_text"
        echo "Apps: current_app / launch_pkg / open_url"
        echo "System: shell <command>"
        exit 1
        ;;
esac

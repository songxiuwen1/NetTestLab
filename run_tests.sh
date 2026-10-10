#!/usr/bin/env bash

# ============================================================
# NetTestLab 最终一键回归脚本
#
# 功能：
# 1. 检查9000端口是否已被旧服务占用
# 2. 自动启动C++ DeviceServer
# 3. 等待服务端真正开始监听
# 4. 激活Python虚拟环境
# 5. 运行全部pytest测试
# 6. 生成HTML测试报告
# 7. 运行benchmark性能测试
# 8. 保存Server、pytest和benchmark结果
# 9. 无论成功或失败，都自动清理DeviceServer
# ============================================================


# -e：普通命令失败时退出
# -u：使用未定义变量时报错
# pipefail：管道中任一命令失败，都认为管道失败
set -euo pipefail


# ------------------------------------------------------------
# 1. 获取项目根目录
# ------------------------------------------------------------

# BASH_SOURCE[0]表示当前脚本文件本身。
# 无论我们从哪个目录调用脚本，都能够找到NetTestLab根目录。
PROJECT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")"
    pwd
)"

cd "$PROJECT_DIR"


# ------------------------------------------------------------
# 2. 创建本次运行所需目录和时间戳
# ------------------------------------------------------------

mkdir -p logs reports

TIMESTAMP=$(date "+%Y%m%d_%H%M%S")


# 每一次测试保留带时间戳的证据
SERVER_LOG="$PROJECT_DIR/logs/server_${TIMESTAMP}.log"
PYTEST_LOG="$PROJECT_DIR/logs/pytest_${TIMESTAMP}.log"

HTML_REPORT="$PROJECT_DIR/reports/pytest_report_${TIMESTAMP}.html"
BENCHMARK_REPORT="$PROJECT_DIR/reports/benchmark_${TIMESTAMP}.txt"


# 同时维护一份固定名称的“最新结果”
FINAL_HTML="$PROJECT_DIR/reports/pytest_report.html"
FINAL_BENCHMARK="$PROJECT_DIR/reports/benchmark.txt"


# ------------------------------------------------------------
# 3. 定义服务端清理函数
# ------------------------------------------------------------

SERVER_PID=""


cleanup() {

    # 只有SERVER_PID已经获得以后才进行清理
    if [[ -n "${SERVER_PID}" ]]; then

        if kill -0 "$SERVER_PID" 2>/dev/null; then

            echo
            echo "[CLEANUP] 正在关闭 DeviceServer，PID=$SERVER_PID"

            # 先尝试正常结束
            kill "$SERVER_PID" 2>/dev/null || true

            # 等待一小段时间让程序退出
            sleep 0.3

            # 如果还没退出，再强制结束
            if kill -0 "$SERVER_PID" 2>/dev/null; then
                echo "[CLEANUP] 服务端仍未退出，执行 kill -9"
                kill -9 "$SERVER_PID" 2>/dev/null || true
            fi
        fi
    fi
}


# 无论脚本正常退出还是中途失败，
# 都执行cleanup，避免9000端口残留旧Server。
trap cleanup EXIT


# ------------------------------------------------------------
# 4. 检查9000端口
# ------------------------------------------------------------

echo "============================================================"
echo " NetTestLab Final Regression"
echo "============================================================"
echo
echo "[1/5] 检查9000端口..."


if ss -lntp | grep -q ":9000"; then

    echo "[ERROR] 9000端口已经被占用。"
    echo
    echo "请先检查："
    echo "  pgrep -af DeviceServer"
    echo "  ss -lntp | grep 9000"
    echo
    echo "确认旧Server关闭后再运行本脚本。"

    exit 1
fi


echo "[OK] 9000端口空闲"


# ------------------------------------------------------------
# 5. 启动C++ DeviceServer
# ------------------------------------------------------------

echo
echo "[2/5] 启动 DeviceServer..."


# 检查可执行文件是否存在
if [[ ! -x "$PROJECT_DIR/server/build/DeviceServer" ]]; then

    echo "[ERROR] 找不到可执行文件："
    echo "server/build/DeviceServer"

    echo
    echo "请先执行："
    echo "cmake -S server -B server/build -DCMAKE_BUILD_TYPE=Debug"
    echo "cmake --build server/build -j"

    exit 1
fi


# 后台启动Server。
# stdout和stderr全部保存到日志。
"$PROJECT_DIR/server/build/DeviceServer" \
    > "$SERVER_LOG" \
    2>&1 &


# $!表示刚刚启动的后台进程PID
SERVER_PID=$!


echo "[INFO] DeviceServer PID=$SERVER_PID"
echo "[INFO] Server日志：$SERVER_LOG"


# ------------------------------------------------------------
# 6. 等待Server真正监听9000端口
# ------------------------------------------------------------

SERVER_READY=0


# 最多检查30次，每次等待0.1秒。
for _ in {1..30}; do

    if ss -lnt | grep -q ":9000"; then

        SERVER_READY=1
        break

    fi


    # 如果Server进程已经提前退出，
    # 就没必要继续等待。
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then

        echo "[ERROR] DeviceServer启动后异常退出。"
        echo
        echo "最近Server日志："

        tail -n 20 "$SERVER_LOG" || true

        exit 1
    fi


    sleep 0.1
done


if [[ "$SERVER_READY" -ne 1 ]]; then

    echo "[ERROR] 等待9000端口超时。"
    exit 1
fi


echo "[OK] DeviceServer已监听9000端口"


# ------------------------------------------------------------
# 7. 激活Python虚拟环境
# ------------------------------------------------------------

echo
echo "[3/5] 激活Python测试环境..."


if [[ ! -f "$PROJECT_DIR/python_tests/.venv/bin/activate" ]]; then

    echo "[ERROR] 找不到Python虚拟环境："
    echo "python_tests/.venv"

    exit 1
fi


source "$PROJECT_DIR/python_tests/.venv/bin/activate"


echo "[OK] Python：$(which python)"


# ------------------------------------------------------------
# 8. 执行全部pytest测试
# ------------------------------------------------------------

echo
echo "[4/5] 开始执行全部pytest测试..."
echo


cd "$PROJECT_DIR/python_tests"


# 这里临时关闭 set -e。
#
# 原因：
# 如果pytest失败，我们仍然需要取得pytest自己的退出码，
# 并打印更清楚的错误信息。
set +e


python -m pytest \
    -v \
    -s \
    --html="$HTML_REPORT" \
    --self-contained-html \
    2>&1 | tee "$PYTEST_LOG"


# PIPESTATUS[0]：
# 获取管道中第一个命令，也就是pytest本身的退出码。
TEST_RESULT=${PIPESTATUS[0]}


# 恢复遇错退出模式
set -e


if [[ "$TEST_RESULT" -ne 0 ]]; then

    echo
    echo "============================================================"
    echo "[FAIL] pytest回归失败"
    echo "退出码：$TEST_RESULT"
    echo "日志：$PYTEST_LOG"
    echo "HTML：$HTML_REPORT"
    echo "============================================================"

    exit "$TEST_RESULT"
fi


# pytest全部通过后，
# 把本次带时间戳报告复制为固定的最终报告名称。
cp "$HTML_REPORT" "$FINAL_HTML"


echo
echo "[OK] pytest全部通过"


# ------------------------------------------------------------
# 9. 执行benchmark性能测试
# ------------------------------------------------------------

echo
echo "[5/5] 开始执行benchmark..."
echo


set +e


# 使用 -m 从 python_tests 根目录按模块运行，
# 这样 benchmark.py 可以正常导入同级的 client 包。
python -m tools.benchmark \
    2>&1 | tee "$BENCHMARK_REPORT"


BENCHMARK_RESULT=${PIPESTATUS[0]}


set -e


if [[ "$BENCHMARK_RESULT" -ne 0 ]]; then

    echo
    echo "[FAIL] benchmark执行失败"
    exit "$BENCHMARK_RESULT"
fi


# 保存一份固定名称的最新benchmark结果。
cp "$BENCHMARK_REPORT" "$FINAL_BENCHMARK"


# ------------------------------------------------------------
# 10. 最终结果
# ------------------------------------------------------------

echo
echo "============================================================"
echo " NetTestLab 最终回归完成"
echo "============================================================"
echo
echo "pytest日志："
echo "  $PYTEST_LOG"
echo
echo "Server日志："
echo "  $SERVER_LOG"
echo
echo "HTML报告："
echo "  $FINAL_HTML"
echo
echo "Benchmark："
echo "  $FINAL_BENCHMARK"
echo
echo "[PASS] 本次一键回归成功"
echo "============================================================"

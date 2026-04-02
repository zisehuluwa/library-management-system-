#!/bin/bash
# 测试运行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}=====================================${NC}"
echo -e "${YELLOW}   图书馆管理系统 - 测试运行脚本   ${NC}"
echo -e "${YELLOW}=====================================${NC}"
echo ""

# 设置 Python 路径
export PATH="/Users/ziwa/Library/Python/3.9/bin:$PATH"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 创建测试报告目录
mkdir -p reports

# 激活测试模式
export TESTING=true

# 解析命令行参数
TEST_MODULE="${1:-all}"

run_all_tests() {
    echo -e "${YELLOW}运行所有测试...${NC}"
    python3 -m pytest tests/ -v --tb=short
}

run_unit_tests() {
    echo -e "${YELLOW}运行单元测试...${NC}"
    python3 -m pytest tests/test_user.py tests/test_book.py -v --tb=short
}

run_api_tests() {
    echo -e "${YELLOW}运行API测试...${NC}"
    python3 -m pytest tests/test_api.py -v --tb=short
}

run_e2e_tests() {
    echo -e "${YELLOW}运行端到端测试...${NC}"
    echo -e "${YELLOW}注意: E2E测试需要 Selenium ChromeDriver${NC}"
    python3 -m pytest tests/test_e2e.py -v --tb=short
}

run_user_tests() {
    echo -e "${YELLOW}运行用户模块测试...${NC}"
    python3 -m pytest tests/test_user.py -v --tb=short
}

run_book_tests() {
    echo -e "${YELLOW}运行图书模块测试...${NC}"
    python3 -m pytest tests/test_book.py -v --tb=short
}

show_help() {
    echo "用法: $0 [模块]"
    echo ""
    echo "可用模块:"
    echo "  all       - 运行所有测试 (默认)"
    echo "  unit      - 运行单元测试"
    echo "  api       - 运行API测试"
    echo "  e2e       - 运行端到端测试"
    echo "  user      - 运行用户模块测试"
    echo "  book      - 运行图书模块测试"
    echo ""
    echo "示例:"
    echo "  $0              # 运行所有测试"
    echo "  $0 unit         # 运行单元测试"
    echo "  $0 api          # 运行API测试"
}

case "$TEST_MODULE" in
    all)
        run_all_tests
        ;;
    unit)
        run_unit_tests
        ;;
    api)
        run_api_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    user)
        run_user_tests
        ;;
    book)
        run_book_tests
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}未知模块: $TEST_MODULE${NC}"
        show_help
        exit 1
        ;;
esac

# 生成覆盖率报告
echo ""
echo -e "${YELLOW}生成测试报告...${NC}"
python3 -m pytest tests/ --cov=. --cov-report=html:reports/coverage --cov-report=term

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}   测试完成！报告已生成${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "报告位置:"
echo "  - 测试报告: reports/test_report.html"
echo "  - 覆盖率报告: reports/coverage/index.html"

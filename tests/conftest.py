"""pytest configuration file to add custom command-line options and modify test collection behavior"""


def pytest_addoption(parser):
    """添加 pytest 命令行选项"""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run live data provider tests (may consume API quota)",
    )


def pytest_collection_modifyitems(config, items):
    """根据命令行选项跳过 live 测试"""
    if not config.getoption("--run-live"):
        import pytest

        skip_live = pytest.mark.skip(reason="需要 --run-live 选项来运行实时数据源测试")
        for item in items:
            # 检查是否有 live 标记
            if item.get_closest_marker("live"):
                item.add_marker(skip_live)

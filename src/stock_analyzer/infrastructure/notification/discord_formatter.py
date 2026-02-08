"""
Discord Markdown 格式转换器

提供 Discord 支持的 Markdown 格式工具方法
参考: https://support.discord.com/hc/en-us/articles/210298617
"""

from typing import Literal


class DiscordMarkdownConverter:
    """
    将标准 Markdown 转换为 Discord 支持的格式
    并提供 Discord Markdown 格式的工具方法

    Discord 支持的格式:
    - 粗体: **text**
    - 斜体: *text* 或 _text_
    - 下划线: __text__
    - 删除线: ~~text~~
    - 标题: # Header, ## Header, ### Header (不支持 #### 及以上)
    - 子文本: -# subtext
    - 链接: [text](url)
    - 列表: - item, * item, 1. item
    - 代码: `code` (单行), ```code``` (多行)
    - 引用: > text (单行), >>> text (多行)
    - 剧透: ||spoiler||
    """

    def convert(self, content: str) -> str:
        """
        转换 Markdown 内容为 Discord 兼容格式
        主要处理:
        1. 降级不支持的四级及以上标题 (#### -> ###)
        2. 转换表格为列表形式
        """
        if not content:
            return ""

        # 1. 降级四级及以上标题
        content = self._downgrade_headers(content)

        # 2. 转换表格
        content = self._convert_tables(content)

        return content

    def _downgrade_headers(self, content: str) -> str:
        """
        将 ####, #####, ###### 降级为 ###
        Discord 只支持 #, ##, ### 三级标题
        """
        import re

        # 匹配行首的 ####, #####, ###### 并替换为 ###
        # 使用正则表达式：行首的 4-6 个 # 号，后接空格
        pattern = r"^(#{4,6})\s"
        replacement = r"### "
        return re.sub(pattern, replacement, content, flags=re.MULTILINE)

    def _convert_tables(self, content: str) -> str:
        """
        将 Markdown 表格转换为 Discord 友好的格式

        对于宽表格（列数较多），使用分行显示：
        - 每行显示 2-3 个字段，避免一行过长
        """
        lines = content.split("\n")
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # 检测表格开始：包含 | 且下一行是分隔符
            if "|" in line and i + 1 < len(lines) and set(lines[i + 1].strip()) <= {"|", "-", " ", ":"}:
                raw_headers = line.split("|")
                headers = [h.strip() for h in raw_headers if h.strip()]

                i += 2  # 跳过标题行和分隔符行

                # 处理所有数据行
                while i < len(lines) and "|" in lines[i]:
                    current_line = lines[i].strip()
                    parts = current_line.split("|")

                    # 去除首尾空元素
                    if current_line.startswith("|"):
                        parts = parts[1:]
                    if current_line.endswith("|"):
                        parts = parts[:-1]

                    row = [p.strip() for p in parts]

                    if len(row) == len(headers):
                        # 根据列数决定显示格式
                        if len(headers) <= 3:
                            # 列数少：一行显示
                            formatted_items = [f"**{h}**: {v}" for h, v in zip(headers, row, strict=False)]
                            new_lines.append(" | ".join(formatted_items))
                        elif len(headers) <= 6:
                            # 中等列数：每行显示 2 个字段
                            for j in range(0, len(headers), 2):
                                end_idx = min(j + 2, len(headers))
                                items = [f"**{headers[k]}**: {row[k]}" for k in range(j, end_idx)]
                                new_lines.append(" | ".join(items))
                            new_lines.append("")  # 行间空行
                        else:
                            # 列数多（如当日行情表）：每行显示 1 个字段
                            for h, v in zip(headers, row, strict=False):
                                new_lines.append(f"**{h}**: {v}")
                            new_lines.append("")  # 行间空行

                    i += 1

            else:
                new_lines.append(lines[i])
                i += 1

        return "\n".join(new_lines)

    # ===== 文本格式方法 =====

    def bold(self, text: str) -> str:
        """粗体格式: **text**"""
        return f"**{text}**"

    def italic(self, text: str) -> str:
        """斜体格式: *text*"""
        return f"*{text}*"

    def underline(self, text: str) -> str:
        """下划线格式: __text__"""
        return f"__{text}__"

    def strikethrough(self, text: str) -> str:
        """删除线格式: ~~text~~"""
        return f"~~{text}~~"

    def bold_italic(self, text: str) -> str:
        """粗斜体格式: ***text***"""
        return f"***{text}***"

    def bold_underline(self, text: str) -> str:
        """粗体+下划线: __**text**__"""
        return f"__**{text}**__"

    def italic_underline(self, text: str) -> str:
        """斜体+下划线: __*text*__"""
        return f"__*{text}*__"

    def bold_italic_underline(self, text: str) -> str:
        """粗斜体+下划线: __***text***__"""
        return f"__***{text}***__"

    def spoiler(self, text: str) -> str:
        """剧透格式: ||text||"""
        return f"||{text}||"

    # ===== 标题方法 =====

    def header(self, text: str, level: Literal[1, 2, 3] = 1) -> str:
        """
        创建 Discord 标题
        注意: # 后面必须有空格
        注意: Discord 只支持 1-3 级标题
        """
        if level > 3:
            level = 3
        hashes = "#" * level
        return f"{hashes} {text}"

    def subtext(self, text: str) -> str:
        """
        创建 Discord 子文本
        注意: -# 后面必须有空格，且必须位于行首
        """
        return f"-# {text}"

    # ===== 链接方法 =====

    def link(self, text: str, url: str) -> str:
        """
        创建 Discord 隐藏链接 (masked link)
        格式: [text](url)
        """
        return f"[{text}]({url})"

    # ===== 代码方法 =====

    def code_inline(self, text: str) -> str:
        """单行代码: `code`"""
        return f"`{text}`"

    def code_block(self, text: str, language: str = "") -> str:
        """
        多行代码块: ```language\ncode```
        支持语言: python, json, markdown, yaml, bash, text 等
        """
        if language:
            return f"```{language}\n{text}\n```"
        return f"```\n{text}\n```"

    # ===== 引用方法 =====

    def quote(self, text: str) -> str:
        """单行引用: > text"""
        lines = text.split("\n")
        return "\n".join(f"> {line}" for line in lines)

    def quote_multi(self, text: str) -> str:
        """多行引用: >>> text（仅第一行需要 >>>）"""
        return f">>> {text}"

    # ===== 列表方法 =====

    def bullet_list(self, items: list[str]) -> str:
        """无序列表: - item"""
        return "\n".join(f"- {item}" for item in items)

    def numbered_list(self, items: list[str]) -> str:
        """有序列表: 1. item"""
        return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))

    # ===== 组合工具方法 =====

    def format_key_value(self, key: str, value: str, bold_key: bool = True) -> str:
        """
        格式化键值对，常用于将表格转换为 Discord 格式
        默认键使用粗体: **key**: value
        """
        if bold_key:
            return f"**{key}**: {value}"
        return f"{key}: {value}"

    def format_section(self, title: str, content: str, title_level: Literal[1, 2, 3] = 2) -> str:
        """
        格式化一个带标题的区块
        """
        header = self.header(title, title_level)
        return f"{header}\n{content}"

    def escape_special_chars(self, text: str) -> str:
        """
        转义 Discord Markdown 特殊字符
        在需要原样显示特殊字符时使用
        """
        special_chars = ["*", "_", "~", "`", ">", "|"]
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

    # ===== 常用模板方法 =====

    def format_alert(self, title: str, message: str, emoji: str = "⚠️") -> str:
        """格式化警告消息"""
        return f"{emoji} **{title}**\n{message}"

    def format_success(self, title: str, message: str) -> str:
        """格式化成功消息"""
        return f"✅ **{title}**\n{message}"

    def format_error(self, title: str, message: str) -> str:
        """格式化错误消息"""
        return f"❌ **{title}**\n{message}"

    def format_info(self, title: str, message: str) -> str:
        """格式化信息消息"""
        return f"ℹ️ **{title}**\n{message}"

    def format_stock_info(
        self,
        stock_name: str,
        stock_code: str,
        current_price: str,
        change_percent: str,
        additional_info: dict[str, str] | None = None,
    ) -> str:
        """
        格式化股票信息的模板
        """
        lines = [
            f"📈 **{stock_name} ({stock_code})**",
            f"现价: {self.bold(current_price)} | 涨跌: {self.bold(change_percent)}",
        ]

        if additional_info:
            lines.append("")  # 空行
            for key, value in additional_info.items():
                lines.append(self.format_key_value(key, value))

        return "\n".join(lines)

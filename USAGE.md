# Linux.do 自动化阅读器使用指南

这是一个用于自动化阅读 [linux.do](https://linux.do) 论坛未读话题的工具。它由三个主要部分组成：

1.  `login_linuxdo.py`: 用于手动登录并保存会话 Cookie。
2.  `read_linuxdo.py`: 使用保存的 Cookie 自动阅读未读话题。
3.  `linuxdo_reader_ui.py`: 一个基于 PyQt5 的图形用户界面，用于方便地管理 Cookie 文件和运行自动化脚本。

## 1. 先决条件

在开始之前，请确保你的系统上安装了以下软件：

*   **Python 3.8+**: 推荐使用最新稳定版本。
*   **uv**: 一个快速的 Python 包安装器和包管理器。
    ```bash
    pip install uv
    ```
*   **Playwright**: 用于浏览器自动化。
    ```bash
    uv pip install playwright
    playwright install
    ```
*   **camoufox**: 一个基于 Playwright 的浏览器自动化库。
    ```bash
    uv pip install camoufox[geoip]
    uv run camoufox fetch
    ```
*   **PyQt5**: 用于构建图形用户界面。
    ```bash
    uv pip install PyQt5
    ```

## 2. 项目结构

确保你的项目目录结构如下：

```
E:/linux.do.auto/
├───login_linuxdo.py
├───read_linuxdo.py
├───linuxdo_reader_ui.py
├───cookies.json (或其他 .json 文件，由登录脚本生成)
├───read_topics.json (由阅读脚本生成)
└───USAGE.md (本文档)
```

## 3. 使用指南

推荐通过 `linuxdo_reader_ui.py` 来管理和运行脚本。

### 3.1 启动 UI

在项目根目录下运行以下命令来启动图形用户界面：

```bash
python linuxdo_reader_ui.py
```

UI 界面将包含两个主要选项卡：`Script Execution` (脚本执行) 和 `Cookie Management` (Cookie 管理)。

### 3.2 Cookie 管理

在 `Cookie Management` 选项卡中，你可以管理用于登录 linux.do 的 Cookie 文件。

*   **选择 Cookie 文件**: 下拉菜单会列出 `E:/linux.do.auto/` 目录下所有 `.json` 文件（`read_topics.json` 除外）。选择你想要使用的 Cookie 文件。
*   **刷新列表**: 如果你手动添加或删除了 Cookie 文件，点击 `Refresh List` 按钮可以更新下拉菜单。
*   **加载选定 Cookie**: 选择文件后，点击 `Load Selected Cookie` 按钮可以查看该 Cookie 文件的内容。
*   **删除选定 Cookie**: 点击 `Delete Selected Cookie` 按钮可以删除当前选中的 Cookie 文件。在删除前会有一个确认提示。
*   **运行登录脚本 (New/Existing)**:
    *   点击此按钮会弹出一个输入框，要求你输入一个文件名来保存 Cookie（例如 `my_account.json`）。
    *   如果你输入一个已存在的文件名，它将覆盖该文件。
    *   如果你输入一个新文件名，它将创建一个新文件。
    *   脚本将启动一个浏览器窗口，并导航到 linux.do 的登录页面。请在此窗口中手动登录你的账户。
    *   登录成功后，脚本会自动保存 Cookie 到你指定的文件中，并关闭浏览器。
    *   **重要**: `login_linuxdo.py` 脚本设计为始终在前台模式运行，以便你进行手动登录。

### 3.3 自动化阅读

在 `Script Execution` 选项卡中，你可以运行自动化阅读脚本。

*   **Headful Mode (前台模式)**: 勾选此复选框，脚本将在可见的浏览器窗口中运行，你可以看到自动化过程。不勾选则在无头模式（后台）运行。
*   **Run Read Script (运行阅读脚本)**:
    *   点击此按钮将启动 `read_linuxdo.py` 脚本。
    *   脚本将使用 `Cookie Management` 选项卡中当前选定的 Cookie 文件进行登录。
    *   它会导航到 linux.do 的未读话题页面，遍历新话题，模拟滚动以加载所有内容，并发送“timings”请求以将话题标记为已读。
    *   已读话题的 URL 将被记录在 `read_topics.json` 文件中，以避免重复阅读。
    *   脚本的输出将显示在下方的文本区域中。
*   **Force Stop (强制终止)**:
    *   当 `Run Read Script` 或 `Run Login Script` 正在运行时，此按钮将启用。
    *   点击此按钮可以强制终止当前正在运行的脚本。请注意，强制终止可能会导致一些资源未完全释放，例如浏览器进程可能不会立即关闭。

## 4. 故障排除

*   **`ModuleNotFoundError`**: 确保你已按照“先决条件”部分安装了所有必要的 Python 包。
*   **`Permission denied`**: 确保脚本对 `E:/linux.do.auto/` 目录及其子文件有读写权限。这通常发生在尝试将目录作为文件打开时，或者权限设置不正确。
*   **Cookie 过期或无效**: 如果 `read_linuxdo.py` 报告 Cookie 过期，请切换到 `Cookie Management` 选项卡，删除旧的 Cookie 文件，然后运行 `Run Login Script` 重新生成新的 Cookie。
*   **脚本无响应**: 如果脚本长时间没有输出或卡住，可以尝试点击 `Force Stop` 按钮来终止它。

## 5. 贡献

如果你有任何改进建议或发现 Bug，欢迎提出！

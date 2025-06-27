![Visitor Count](https://profile-counter.glitch.me/waterfeet/count.svg)

![](https://github-readme-stats.vercel.app/api?username=waterfeet&show_icons=true&theme=transparent)

## DoroPet
一个Doro的桌面宠物，基于python和PyQt5，适配deepseek、Maas星火、千问、Gemini的api接口，自定义人格对话

### V2.1
1.移除原有天气，直接导入hefeng天气web界面。探索了更灵活的网页内容显示。

2.添加人格市场，支持手动配置网址，用于提供更优质的人格提示词获取。

3.新增live2d配置界面，可导入预览并应用到桌宠。

4.全新的LLM服务配置界面。可支持传统的OPENAI接口。可以自由配置相同服务商的不同模型接口。（该页面此版本下只实现了基础功能，交互性有待提升）


### V2.0
1.宠物主体改为Live2d模型，模型作者请见[Bilibili - 0x4682B4](https://www.bilibili.com/video/BV16z421B7HQ/?spm_id_from=333.337.search-card.all.click&vd_source=9bceeddd42a92116ea7719803b25e80f)
支持自动导入表情、动作。右键菜单切换
![示例1](https://github.com/waterfeet/DoroPet_V2/blob/main/%E8%A1%A8%E6%83%85.png)

![示例2](https://github.com/waterfeet/DoroPet_V2/blob/main/%E5%8A%A8%E4%BD%9C.png)

2.新增知心天气api获取
![示例3](https://github.com/waterfeet/DoroPet_V2/blob/main/%E7%A4%BA%E4%BE%8B_%E5%A4%A9%E6%B0%94.png)

3.新增连连看小游戏
![示例4](https://github.com/waterfeet/DoroPet_V2/blob/main/%E8%BF%9E%E8%BF%9E%E7%9C%8B.png)

4.通用参数新增前台启动，方便直播的时候获取窗口进程


### V1.2
1.修复右键菜单中快捷聊天和自动切换的勾选显示错误，现在两个功能只能生效一个


### V1.1
1.新增Gemini适配，但是使用了openAI兼容模式，请勿填错信息，如果无响应，也可尝试检查网络环境

2.新增自动随机行为，每隔一段时间，会从（跳一下、切换动画、随机发言）中随机选择一种行为执行，与下一个功能会互斥

3.新增快捷聊天功能，在Doro下方生成输入框，发送消息后，Doro上方会生成一个回复，同时同步到聊天主对话框

### V1.0
实现基本功能

## 界面展示
![示例1](https://github.com/waterfeet/DoroPet/blob/main/%E7%A4%BA%E4%BE%8B1.png)

![示例2](https://github.com/waterfeet/DoroPet/blob/main/%E7%A4%BA%E4%BE%8B2.png)

## 使用注意
启用大模型聊天，需要在设置界面设置
![示例3](https://github.com/waterfeet/DoroPet/blob/main/%E7%A4%BA%E4%BE%8B3.png)

## 模型获取地址
Maas
[直达](https://training.xfyun.cn/experience/text2text)

DeepSeek
[直达](https://platform.deepseek.com)

通义千问
[直达](https://bailian.console.aliyun.com/?spm=5176.30202035.J_5cDGbYTFXDvcuWnwVDdx7.1.370f1e71U1iaYl&tab=model#/model-market/detail/qwen3)

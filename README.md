# vibe-video

一个 [Claude Code](https://claude.com/claude-code) skill：用 Remotion 做音乐卡点的动画视频。适合知识科普，也适合剧情短片。视频没有配音，只有中文字幕或台词；换场落在重拍上，关键动作配上用代码合成的音效。流程是先交 10 秒试片，再逐段制作。

## 安装

```bash
git clone https://github.com/xiaochangtongxue/vibe-video ~/.claude/skills/vibe-video
```

依赖：Node.js、Python 3、FFmpeg，以及 `pip install numpy librosa`。

## 使用

在 Claude Code 里说「做一个讲 XX 的科普视频」或「做一段 XX 的剧情动画」，并给出一首音乐。具体流程见 [SKILL.md](SKILL.md)。

## 音乐

仓库不附带音乐文件。[assets/MUSIC.md](assets/MUSIC.md) 里四首曲目的拍点已经预先算好：你提供的音频和记录的 SHA-256 一致时直接使用，其他音乐会自动分析拍点。

## 许可

代码以 MIT 许可发布，见 [LICENSE](LICENSE)。本项目基于 [xiaominggpT7890/vibe-bgm-skill](https://github.com/xiaominggpT7890/vibe-bgm-skill) 改写，We Never 的拍点缓存也来自这个项目，其 MIT 许可见 [LICENSE-vibe-bgm-skill.txt](LICENSE-vibe-bgm-skill.txt)。音乐权利归各自的权利方。

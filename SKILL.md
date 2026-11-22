---
name: vibe-video
description: 用 Remotion 做音乐卡点的动画视频，题材可以是知识科普，也可以是剧情短片（玄幻、热血、反转等）：无配音、中文字幕或台词、画面换场落在重拍上、关键动作配代码合成音效，先交 10 秒试片再逐段制作。用户要做「知识视频」「科普视频」「剧情动画」「动画短片」「卡点视频」「Vibe 知识大赏风格」「Remotion 视频配音乐」时使用。不用于纯剪辑现成素材或带真人配音的视频。
---

# Vibe 卡点动画视频（Remotion）

用户需要给出**主题或故事**，音乐可选。`assets/MUSIC.md` 里的五首（《We Never · 若如初见》《把回忆拼好给你》及其慢节奏版、《寂寞烟火》《起风了》）预先算好了拍点，段落地图也在该文件。仓库不附带音乐文件：`assets/` 里放着对应 mp3 时，它们就是内置曲目，可以让用户直接挑；没有的话请用户提供一首音乐，与记录的 SHA-256 一致时直接用预算拍点，否则自动分析。以下四步按顺序执行，每步完成再进下一步。下文 `$SKILL` 指本 Skill 目录；Windows 上 `python3` 写作 `python`。

Remotion 的 API 用法（字体加载、运动模糊、视频和图片素材、透明视频、渲染参数等）以官方 skill `remotion-best-practices` 为准；没装时提示用户 `npx skills add remotion-dev/skills`。本 Skill 只管卡点、导演和音效。

## 1. 定规格

默认：1920×1080、30fps、16:9；无配音，中文短句字幕：科普讲清知识点，剧情写台词、旁白或诗句。**先和用户确认目标时长**（这类视频常见 2 分钟左右），再按「时长 ÷ 每小节秒数」算出总小节数和分段数，不要默认铺满整首歌。视频比音乐短时，模板会在最后 1.5 秒自动把音乐淡出。用户明确要竖屏时加 `--ratio 9:16`（模板示例段按横屏构图，竖屏需重新构图）。

```bash
python3 $SKILL/scripts/new_project.py <项目目录> [--audio <音乐文件>] [--ratio 9:16]
cd <项目目录> && npm install
```

`assets/we-never.mp3` 存在时可以省略 `--audio`，默认用它；内置的其他曲目写 `--audio $SKILL/assets/<文件>`。脚本会复制模板、放入音乐、生成 `public/beats.json` 和示例音效。`assets/MUSIC.md` 里的曲目靠 SHA-256 匹配直接用预算好的拍点；其他音乐自动运行 `analyze.py`（需要 FFmpeg、numpy、librosa）。

动手做第一段前，先按 [references/directing.md](references/directing.md) 的「文案」一节写出全片字幕，定好开头钩子和结尾金句，给用户过一遍。

## 2. 卡点

先读 `public/beats.json`，向用户报告：BPM、调性、前几个重拍的秒数、`downbeatConfidence`。

- `beats[]` 每拍带 `bar`、`beatInBar`、`downbeat`。**重拍是推断出来的**（低频冲击 + 和声变化最集中的相位），不是标注。置信度低于约 0.5，或用户试听后说没对上，用 `analyze.py <音乐> --out public/beats.json --downbeat-phase N` 手动改相位。
- `onsets[]`（打击性起音）和 `tonalOnsets[]`（带音高的起音）用于局部变化。
- 分层规则：**整屏换场、主要动作落定在重拍上**；关键词出现、描边、局部抖动跟拍点和起音走。不要只跟重拍变（画面呆），也不要每个起音都切屏（画面乱）。
- 不按 BPM 均匀推算时间；一律从 `beats.json` 取真实时间。

分段写在 `src/segments.json`：`{"id": "02", "fromBar": 5, "toBar": 10}`，起止都是小节号，分段边界天然落在重拍上。110 BPM 左右一小节约 2 秒。

## 3. 配音效

音效清单在 `src/sfx.json`，音高用调内级数（`degree` 1–7），保证不和旋律打架：

```bash
python3 $SKILL/scripts/sfx.py --manifest src/sfx.json --beats public/beats.json --outdir public/sfx
```

音色：`pluck` `bell` `marimba` `piano`（有音高）、`kick` `tick` `whoosh` `riser` `blade` `boom`。音色选与画面动作契合的：物体落地用 `kick`/`marimba`，出现概念用 `bell`/`pluck`，转场用 `whoosh`，蓄力用 `riser`，刀剑出鞘、斩击用 `blade`，重击、盖印、爆发用 `boom`。只给关键动作配，不给每条字幕配。字幕、诗句、台词出现时不配有音高的音效：合成的拨弦和铃声听着廉价，还和歌的旋律抢。改了音乐必须重跑这条命令（调变了）。

在段文件里导出 `sfx: Cue[]`，`atMs` 用拍点时间，和动作落定同一时刻。

## 4. 试片

1. 先做 `segments.json` 的第一段（约 10 秒），渲染给用户看：`npx remotion render seg-01 out/seg-01.mp4`。也可以 `npm run studio` 实时预览。
2. 用户确认后再一段一段往下做；每段一个 `src/segments/Sxx.tsx`，在 `src/segments/index.ts` 注册。
3. 哪段不好只改那一段，重渲 `seg-xx`。每做完一段只渲这一段，不要每段都渲整片：加了景深和运动模糊后，整片要渲好几分钟。段间衔接用切点前后几帧检查，必要时渲相邻两段。全部完成或用户要求时，再 `npm run render` 出整片。

## 写段文件

读 [references/directing.md](references/directing.md) 的镜头写法。可用工具：

- 段内小节一律写成相对 `startBar('xx')` 的偏移（`bar(BAR0 + 2, 1)`），不写绝对小节号。这样删段、调顺序时只改 `segments.json`，再修一下新衔接处的承接物起点就行。
- `src/timeline.ts`：`useSongFrame()`（当前在整首歌里的帧，音乐是唯一时钟）、`bar(n, beatInBar)`、`beatsIn()`、`hitsIn(onsets|tonalOnsets, from, to, minStrength)`、`msToFrame()`。
- `src/motion.ts`：`landAt(frame, atMs, leadMs)` 提前开始、在拍点那一帧落定；`after()` 拍点之后的动作；`pulse()` 拍点冲击衰减；`countReached()` 累计计数。
- 判断「是否已到某拍点」要用帧比较（`f >= msToFrame(t)`），不要拿 `f / FPS * 1000` 和毫秒比：拍点所在那一帧取整后可能早于拍点十几毫秒，查「上一拍」时会拿到 -1。
- `src/components/Caption.tsx`：短句字幕，【】包住的词高亮。
- `src/theme.ts`：配色和字体。

`src/segments/S01.tsx` 是完整示例（声音让玻璃共振碎裂），演示卡点手法；它是简化的线框风格，成片质感按 directing.md 的「质感」「镜头」两节做。做真实主题时替换掉。

## 交付前核对

- 第 1 秒就有钩子；片尾安静部分不超过约 3 秒，停在金句上。
- 每次整屏变化都落在重拍上（在 Studio 里逐帧看拍点那一帧）；约每两小节有一次镜头或构图变化。
- 字幕一次一句，能读完再换，约每小节一句，一句最多停两小节；画面里的标签用完就淡出；重要概念字最大。
- 音效和动作同帧，音量不盖过音乐。成品音乐多数压到 0 dBFS，所以模板把音乐设为 0.6，音效 `volume` 不超过 0.6；渲染后测峰值，应低于 0 dB：`ffmpeg -i out/seg-01.mp4 -af volumedetect -vn -f null - 2>&1 | grep max_volume`
- 不承诺流量，不编造歌曲作者或授权信息。预算拍点曲目的来源见 `assets/MUSIC.md`。
